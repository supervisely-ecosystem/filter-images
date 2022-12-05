from fastapi import Depends, HTTPException

import supervisely

import src.filtering.widgets as card_widgets
import src.filtering.functions as card_functions
import src.images_table.functions as table_functions
import src.images_table.widgets as table_widgets

from supervisely.app import DataJson, StateJson
from supervisely.app.widgets import ElementButton
from supervisely import logger

import src.sly_globals as g
import asyncio


def apply_filters_long(state: supervisely.app.StateJson):
    StateJson()['filtering'] = True
    StateJson().send_changes()
    try:
        query = card_functions.build_queries_from_filters(state)
        g.images_list = card_functions.get_images(query)
    except Exception as e:
        StateJson()['filtering'] = False
        StateJson().send_changes()
        raise HTTPException(500, repr(e))
    if len(g.images_list) == 0:
        StateJson()["empty_list"] = True
        StateJson()['filtering'] = False
        StateJson().send_changes()
        return
    else:
        StateJson()["empty_list"] = False
    if len(g.images_list) > g.TABLE_IMAGES_LIMIT:
        table_images = g.images_list[:g.TABLE_IMAGES_LIMIT]
        StateJson()['show_images_limit_warn'] = True
    else:
        table_images = g.images_list
    DataJson()["images_list_len"] = len(g.images_list)
    table_functions.fill_table(table_images)
    first_row = table_widgets.images_table.get_json_data()['table_data']['data'][0]
    id_col_index = table_widgets.images_table.get_json_data()['table_data']['columns'].index('id')
    table_functions.show_preview(first_row[id_col_index]) 
    DataJson().send_changes()
    StateJson()['dstDatasetName'] = 'ds0'
    StateJson()['filtering'] = False
    StateJson()['apply_text'] = f'APPLY TO {DataJson()["images_list_len"]} IMAGES'

    StateJson()['current_step'] += 2
    StateJson()['collapsed_steps']["images_table"] = False
    StateJson()['collapsed_steps']["actions"] = False
    StateJson().send_changes()


def filtering_finished(future):
    if future.exception():
        logger.warn(repr(future.exception()))
    else:
        print("action finished")
    

@g.app.post('/apply_filters/')
def apply_filters_clicked(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    my_future = g.loop.run_in_executor(g.executor, apply_filters_long, state)
    task = asyncio.ensure_future(my_future, loop=g.loop)
    task.add_done_callback(filtering_finished)
    

@g.app.post('/add_filter/')
def add_filter_clicked(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    StateJson()['selected_filters'].append(DataJson()['default_filter'])
    StateJson()['current_preset'] = 'Custom'
    StateJson().send_changes()


@g.app.post('/remove_all_filters/')
def remove_all_filters_clicked(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    StateJson()['selected_filters'] = []
    StateJson()['current_preset'] = DataJson()['available_presets'][0]['name']  # All images
    StateJson().send_changes()


@g.app.post('/select_preset/')
def selected_preset_changed(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    if StateJson()['current_preset'] == 'Custom':
        return
    current_preset_filters = None
    for preset in DataJson()['available_presets']:
        if preset['name'] == state['current_preset']:
            current_preset_filters = preset["filters"]
    if current_preset_filters is None:
        supervisely.logger.warn(f"Not found filters for preset: {state['current_preset']}")
        current_preset_filters = []
    StateJson()['selected_filters'] = current_preset_filters
    StateJson().send_changes()


@g.app.post('/select_filter/')
def selected_filter_changed(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    selected_filter_name = state['selected_filters'][state['filter_to_change']]['name']
    selected_filter = None

    for filter in DataJson()['available_filters']:
        if filter['name'] == selected_filter_name:
            selected_filter = filter
    if selected_filter is None:
        supervisely.logger.warn(f"Not found filter with name: {state['selected_filter']}")
        selected_filter = DataJson()['default_filter']
    StateJson()['selected_filters'][state['filter_to_change']] = selected_filter
    StateJson().send_changes()


@g.app.post('/remove_filter/')
def remove_filter_clicked(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    StateJson()['selected_filters'].pop(state['filter_to_change'])
    if len(state['selected_filters']) == 0:
        StateJson()['current_preset'] = DataJson()['available_presets'][0]['name']  # All images
    else:
        StateJson()['current_preset'] = 'Custom'
    StateJson().send_changes()

@card_widgets.reselect_filters_button.add_route(app=g.app, route=ElementButton.Routes.BUTTON_CLICKED)
def reselect_filters_button_clicked(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    StateJson()['selected_filters'] = []
    StateJson()['current_preset'] = DataJson()['available_presets'][0]['name']  # All images
    StateJson()['current_step'] = DataJson()["steps"]["filtering"]

    StateJson().send_changes()

@g.app.post('/select_tag/')
def selected_filter_changed(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    new_tag_id = state['selected_filters'][state['filter_to_change']]['data']['tagId']
    tag_data = None
    for tag in DataJson()['available_tags']:
        if tag['id'] == new_tag_id:
            tag_data = tag
            break

    if tag_data is None:
        supervisely.logger.warn(f"Not found tag with id: {new_tag_id}")
        tag_data = DataJson()['available_tags'][0]

    StateJson()['selected_filters'][state['filter_to_change']]['data']['valueType'] = tag_data['value_type']

    if tag_data['value_type'] == str(supervisely.TagValueType.ANY_NUMBER):
        StateJson()['selected_filters'][state['filter_to_change']]['data']['value'] = {
            'from': 0.0, 
            'to': 1.0
        }
    elif tag_data['value_type'] == str(supervisely.TagValueType.ANY_STRING):
        StateJson()['selected_filters'][state['filter_to_change']]['data']['value'] = ''
    elif tag_data['value_type'] == str(supervisely.TagValueType.ONEOF_STRING):
        StateJson()['available_tag_values'] = tag_data["values"]
        StateJson()['selected_filters'][state['filter_to_change']]['data']['value'] = []
    elif tag_data['value_type'] == str(supervisely.TagValueType.NONE):
        StateJson()['selected_filters'][state['filter_to_change']]['data']['value'] = None
    StateJson().send_changes()
