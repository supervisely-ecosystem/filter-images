from fastapi import Depends, HTTPException

import supervisely

import src.actions.widgets as card_widgets
import src.actions.functions as card_functions
import src.input_project.widgets as input_project_widgets

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
        card_widgets.warning_before_action.description = "Your source project data WILL BE CHANGED. Apply this action only if you're sure that all settings selected correctly."
    elif state['selected_action'] == 'Delete':
        state['apply_text'] = f'DELETE {num_images} IMAGES'
        card_widgets.warning_before_action.description = "Your source project data WILL BE DELETED. Apply this action only if you're sure what you do."
    elif state['selected_action'] == 'Assign tag':
        state['apply_text'] = f'ASSIGN TAG TO {num_images} IMAGES'
        card_widgets.warning_before_action.description = "Your source project data WILL BE CHANGED. Apply this action only if you're sure what you do."
    elif state['selected_action'] == 'Remove all tags':
        state['apply_text'] = f'REMOVE TAGS FROM {num_images} IMAGES'
        card_widgets.warning_before_action.description = "Your source project data WILL BE CHANGED. Apply this action only if you're sure what you do."
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
    input_project_widgets.project_selector.update_data()
    run_sync(state.synchronize_changes())
    run_sync(DataJson().synchronize_changes())

@g.app.post('/select_tag_to_assign/')
def tag_to_assign_selected(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    if state['assign_tag_is_existing'] == 'true':
        if state['tag_to_assign'] is None:
            return
        new_tag_id = state['tag_to_assign']
        tag_data = None
        for tag in DataJson()['available_tags']:
            if tag['id'] == new_tag_id:
                tag_data = tag
                break

        if tag_data is None:
            supervisely.logger.warn(f"Not found tag with id: {new_tag_id}")
            tag_data = DataJson()['available_tags'][0]

        state['tag_to_assign_value_type'] = tag_data['value_type']

    if state['tag_to_assign_value_type'] == str(supervisely.TagValueType.ANY_NUMBER):
        state['tag_to_assign_value'] = 0
    elif state['tag_to_assign_value_type'] == str(supervisely.TagValueType.ANY_STRING):
        state['tag_to_assign_value'] = ''
    elif state['tag_to_assign_value_type'] == str(supervisely.TagValueType.ONEOF_STRING):
        # TODO: bug when new tag (currently not implemented)
        state['tag_to_assign_values'] = tag_data["values"]
        state['tag_to_assign_value'] = state['tag_to_assign_values'][0]
    elif state['tag_to_assign_value_type'] == str(supervisely.TagValueType.NONE):
        state['tag_to_assign_value'] = None
    run_sync(state.synchronize_changes())