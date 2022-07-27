from fastapi import Depends, HTTPException

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
    try:
        res_project_info, res_dataset_msg = card_functions.apply_action(state)
        state["action_process"] = False
        state["action_finished"] = True
        run_sync(state.synchronize_changes())

        if res_project_info.reference_image_url is not None:
            DataJson()['dstProjectPreviewUrl'] = g.api.image.preview_url(
                res_project_info.reference_image_url, 
                100, 
                100
            )
        DataJson()['dstDatasetMsg'] = res_dataset_msg
        DataJson()['dstProjectName'] = res_project_info.name
        DataJson()['dstProjectId'] = res_project_info.id

        run_sync(DataJson().synchronize_changes())
    except Exception as e:
        state["action_process"] = False
        
        run_sync(state.synchronize_changes())
        run_sync(DataJson().synchronize_changes())
        raise HTTPException(500, repr(e))
        

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

@g.app.post('/select_action/')
def dst_project_selected(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    num_images = len(DataJson()['images_list'])
    if state['selected_action'] == 'Copy / Move':
        state['apply_text'] = f'APPLY TO {num_images} IMAGES'
        card_widgets.warning_before_action.title = "Your source project data MAY BE CHANGED. Apply this action only if you're sure that all settings selected correctly."
    elif state['selected_action'] == 'Delete':
        state['apply_text'] = f'DELETE {num_images} IMAGES'
        card_widgets.warning_before_action.title = "Your source project data WILL BE DELETED. Apply this action only if you're sure what you do."
    elif state['selected_action'] == 'Assign tag':
        state['apply_text'] = f'ASSIGN TAG TO {num_images} IMAGES'
        card_widgets.warning_before_action.title = "Your source project data WILL BE CHANGED. Apply this action only if you're sure what you do."
    elif state['selected_action'] == 'Remove all tags':
        state['apply_text'] = f'REMOVE TAGS FROM {num_images} IMAGES'
        card_widgets.warning_before_action.title = "Your source project data WILL BE CHANGED. Apply this action only if you're sure what you do."
    run_sync(state.synchronize_changes())
    run_sync(DataJson().synchronize_changes())

@g.app.post('/finish_app/')
def dst_project_selected(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    f.shutdown_app()

@g.app.post('/new_action/')
def dst_project_selected(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    state["action_finished"] = False
    state['current_step'] = 1
    state['collapsed_steps'] = {
        "input_project": False,
        "filtering": True,
        "images_table": True,
        "actions": True
    }
    state['scrollIntoView'] = 'pageTop'
    run_sync(state.synchronize_changes())