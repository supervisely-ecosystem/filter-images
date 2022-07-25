from fastapi import Depends, HTTPException
from numpy import False_

import supervisely

import src.actions.widgets as card_widgets
import src.actions.functions as card_functions

from supervisely.app import DataJson, StateJson
from supervisely.app.fastapi import run_sync
from supervisely.app.widgets import ElementButton

import src.sly_functions as f

import src.sly_globals as g


@g.app.post('/apply_action/')
def apply_action_clicked(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    state["action_process"] = True
    run_sync(state.synchronize_changes())
    res_project_info, res_dataset_msg = card_functions.apply_action(state)
    state["action_process"] = False
    state["action_finished"] = True

    DataJson()['dstProjectPreviewUrl'] = g.api.image.preview_url(
        res_project_info.reference_image_url, 
        100, 
        100
    )
    DataJson()['dstDatasetMsg'] = res_dataset_msg
    DataJson()['dstProjectName'] = res_project_info.name
    run_sync(state.synchronize_changes())
    run_sync(DataJson().synchronize_changes())

    f.shutdown_app()

@g.app.post('/select_dst_project/')
def dst_project_selected(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    state['loadingDatasets'] = True
    run_sync(state.synchronize_changes())
    datasets = g.api.dataset.get_list(state['selectedProjectId'])
    DataJson()['available_dst_datasets'] = [dataset.name for dataset in datasets]
    run_sync(DataJson().synchronize_changes())
    state['selectedDatasetName'] = DataJson()['available_dst_datasets'][0]
    for i in range(len(DataJson()['available_dst_datasets']) + 1):
        if f'ds{i}' not in DataJson()['available_dst_datasets']:
            state['dstDatasetName'] = f'ds{i}'
            break
    state['loadingDatasets'] = False
    run_sync(state.synchronize_changes())
