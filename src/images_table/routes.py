from fastapi import Depends, HTTPException

import src.sly_globals as g
from supervisely.app import DataJson, StateJson
from supervisely.app.fastapi import run_sync

import src.images_table.widgets as card_widgets
import src.images_table.functions as card_functions
from supervisely.app.widgets.classic_table.classic_table import ClassicTable

@card_widgets.images_table.add_route(app=g.app, route=ClassicTable.Routes.CELL_CLICKED)
def images_table_cell_clicked(state: StateJson = Depends(StateJson.from_request)):
    if state['loading_preview']:
        return
    state['loading_preview'] = True
    run_sync(state.synchronize_changes())
    selected_cell = card_widgets.images_table.get_selected_cell(state)
    if selected_cell is None:
        return
    
    card_functions.show_preview(selected_cell['row_data']['id'], state)
    state['loading_preview'] = False
    run_sync(DataJson().synchronize_changes())
    run_sync(state.synchronize_changes())


