from fastapi import Depends, HTTPException

import supervisely

import src.filtering.widgets as card_widgets
import src.filtering.functions as card_functions
import src.images_table.functions as table_functions
import src.images_table.widgets as table_widgets

from supervisely.app import DataJson, StateJson
from supervisely.app.fastapi import run_sync
from supervisely.app.widgets import ElementButton

import src.sly_globals as g


@g.app.post('/apply_filters/')
def apply_filters_clicked(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    state['filtering'] = True
    run_sync(state.synchronize_changes())
    query = card_functions.build_queries_from_filters(state)
    try:
        images_list = card_functions.get_images(query)
    except Exception as e:
        raise HTTPException(500, repr(e))
    if len(images_list) == 0:
        state["empty_list"] = True
        state['filtering'] = False
        run_sync(state.synchronize_changes())
        return
    else:
        state["empty_list"] = False
    DataJson()['images_list'] = images_list
    table_functions.fill_table(images_list)
    first_row = table_widgets.images_table.get_json_data()['table_data']['data'][0]
    id_col_index = table_widgets.images_table.get_json_data()['table_data']['columns'].index('id')
    table_functions.show_preview(first_row[id_col_index], state) 
    
    state['dstDatasetName'] = 'ds0'
    state['filtering'] = False
    state['apply_text'] = f'APPLY TO {len(images_list)} IMAGES'

    state['current_step'] += 2
    state['collapsed_steps']["images_table"] = False
    state['collapsed_steps']["actions"] = False
    run_sync(state.synchronize_changes())
    run_sync(DataJson().synchronize_changes())


@g.app.post('/add_filter/')
def add_filter_clicked(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    state['selected_filters'].append(DataJson()['default_filter'])
    state['objects_count_buttons_visible'].append(True)
    state['current_preset'] = 'Custom'
    run_sync(state.synchronize_changes())


@g.app.post('/remove_all_filters/')
def remove_all_filters_clicked(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    state['selected_filters'] = []
    state['objects_count_buttons_visible'] = []
    state['current_preset'] = DataJson()['available_presets'][0]['name']  # All images
    run_sync(state.synchronize_changes())


@g.app.post('/select_preset/')
def selected_preset_changed(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    if state['current_preset'] == 'Custom':
        return
    current_preset_filters = None
    for preset in DataJson()['available_presets']:
        if preset['name'] == state['current_preset']:
            current_preset_filters = preset["filters"]
    if current_preset_filters is None:
        supervisely.logger.warn(f"Not found filters for preset: {state['current_preset']}")
        current_preset_filters = []
    state['selected_filters'] = current_preset_filters
    state['objects_count_buttons_visible'] = [True] * len(state['selected_filters'])
    run_sync(state.synchronize_changes())


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
    state['selected_filters'][state['filter_to_change']] = selected_filter
    state['objects_count_buttons_visible'][state['filter_to_change']] = True
    run_sync(state.synchronize_changes())


@g.app.post('/remove_filter/')
def remove_filter_clicked(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    state['selected_filters'].pop(state['filter_to_change'])
    state['objects_count_buttons_visible'].pop(state['filter_to_change'])
    if len(state['selected_filters']) == 0:
        state['current_preset'] = DataJson()['available_presets'][0]['name']  # All images
    else:
        state['current_preset'] = 'Custom'
    run_sync(state.synchronize_changes())


@g.app.post('/open_object_counts/')
def open_object_counts_clicked(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    state['objects_count_buttons_visible'][state['filter_to_change']] = False
    run_sync(state.synchronize_changes())

@card_widgets.reselect_filters_button.add_route(app=g.app, route=ElementButton.Routes.BUTTON_CLICKED)
def reselect_filters_button_clicked(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    state['selected_filters'] = []
    state['objects_count_buttons_visible'] = []
    state['current_preset'] = DataJson()['available_presets'][0]['name']  # All images

    DataJson()['current_step'] = DataJson()["steps"]["filtering"]

    run_sync(DataJson().synchronize_changes())
    run_sync(state.synchronize_changes())
