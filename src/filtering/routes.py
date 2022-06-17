from fastapi import Depends, HTTPException

import supervisely

import src.filtering.widgets as card_widgets
import src.filtering.functions as card_functions
from supervisely import sly_logger

from supervisely.app import DataJson, StateJson
from supervisely.app.fastapi import run_sync
from supervisely.app.widgets import ElementButton

import src.sly_globals as g

@card_widgets.apply_filters_button.add_route(app=g.app, route=ElementButton.Routes.BUTTON_CLICKED)
def apply_filters_button_clicked(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    query = card_functions.build_query_from_filters()
    images_list = card_functions.get_images(query)
    card_functions.fill_table(images_list)
    card_functions.show_preview()

@card_widgets.add_filter_button.add_route(app=g.app, route=ElementButton.Routes.BUTTON_CLICKED)
def add_filter_button_clicked(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    state['selected_filters'].append(DataJson()['default_filter'])
    run_sync(state.synchronize_changes())

@card_widgets.remove_all_filters_button.add_route(app=g.app, route=ElementButton.Routes.BUTTON_CLICKED)
def remove_all_filters_button_clicked(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    state['selected_filters'] = []
    run_sync(state.synchronize_changes())

@g.app.post('/select_preset/')
def selected_preset_changed(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    current_preset_filters = None
    for preset in DataJson()['available_presets']:
        if preset['name'] == state['current_preset']:
            current_preset_filters = preset["filters"]
    if current_preset_filters is None:
        supervisely.logger.warn(f"Not found filters for preset: {state['current_preset']}")
        current_preset_filters = []
    state['selected_filters'] = current_preset_filters
    run_sync(state.synchronize_changes())