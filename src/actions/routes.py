from fastapi import Depends, HTTPException

import supervisely

import src.actions.widgets as card_widgets
import src.actions.functions as card_functions
import src.input_project.widgets as input_project_widgets
import src.filtering.functions as filtering_functions

from supervisely.app import DataJson, StateJson

import src.sly_functions as f

from supervisely import logger

import src.sly_globals as g
import asyncio


def apply_action_long(state: supervisely.app.StateJson):
    StateJson()["action_process"] = True
    StateJson().send_changes()
    queries = filtering_functions.build_queries_from_filters(state)
    g.images_list = filtering_functions.get_images(queries, with_limit=False)
    try:
        res_project_info, res_dataset_msg = card_functions.apply_action(state)
        StateJson()["action_process"] = False
        StateJson()["action_finished"] = True
        StateJson().send_changes()

        if res_project_info.reference_image_url is not None:
            DataJson()["dstProjectPreviewUrl"] = g.api.image.preview_url(
                res_project_info.reference_image_url, 100, 100
            )
        DataJson()["dstDatasetMsg"] = res_dataset_msg
        DataJson()["dstProjectName"] = res_project_info.name
        DataJson()["dstProjectId"] = res_project_info.id

        DataJson().send_changes()
    except Exception as e:
        StateJson()["action_process"] = False

        StateJson().send_changes()
        DataJson().send_changes()
        raise HTTPException(500, repr(e))


def action_finished(future):
    if future.exception():
        logger.warn(repr(future.exception()))
    else:
        print("action finished")


@g.app.post("/apply_action/")
def apply_action_clicked(
    state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request),
):
    my_future = g.loop.run_in_executor(g.executor, apply_action_long, state)
    task = asyncio.ensure_future(my_future, loop=g.loop)
    task.add_done_callback(action_finished)


@g.app.post("/select_dst_project/")
def dst_project_selected(
    state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request),
):
    StateJson()["loadingDatasets"] = True
    StateJson().send_changes()
    datasets = g.api.dataset.get_list(state["selectedProjectId"])
    DataJson()["available_dst_datasets"] = [dataset.name for dataset in datasets]
    DataJson().send_changes()
    StateJson()["selectedDatasetName"] = DataJson()["available_dst_datasets"][0]
    for i in range(len(DataJson()["available_dst_datasets"]) + 1):
        if f"ds{i}" not in DataJson()["available_dst_datasets"]:
            StateJson()["dstDatasetName"] = f"ds{i}"
            break
    StateJson()["loadingDatasets"] = False
    StateJson().send_changes()


@g.app.post("/select_action/")
def dst_project_selected(
    state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request),
):
    num_images = DataJson()["images_list_len"]
    if state["selected_action"] == "Copy / Move":
        StateJson()["apply_text"] = f"APPLY TO {num_images} IMAGES"
        card_widgets.warning_before_action.description = "Your source project data WILL BE CHANGED. Apply this action only if you're sure that all settings selected correctly."
    elif state["selected_action"] == "Delete":
        StateJson()["apply_text"] = f"DELETE {num_images} IMAGES"
        card_widgets.warning_before_action.description = "Your source project data WILL BE DELETED. Apply this action only if you're sure what you do."
    elif state["selected_action"] == "Assign tag":
        StateJson()["apply_text"] = f"ASSIGN TAG TO {num_images} IMAGES"
        card_widgets.warning_before_action.description = "Your source project data WILL BE CHANGED. Apply this action only if you're sure what you do."
    elif state["selected_action"] == "Remove all tags (from images)":
        StateJson()["apply_text"] = f"REMOVE ALL TAGS FROM {num_images} IMAGES"
        card_widgets.warning_before_action.description = "Your source project data WILL BE CHANGED. Apply this action only if you're sure what you do."
    elif state["selected_action"] == "Remove specific tag (from images)":
        StateJson()["apply_text"] = f"REMOVE SPECIFIED TAG FROM {num_images} IMAGES"
        card_widgets.warning_before_action.description = "Your source project data WILL BE CHANGED. Apply this action only if you're sure what you do."
    StateJson().send_changes()
    DataJson().send_changes()


@g.app.post("/finish_app/")
def dst_project_selected(
    state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request),
):
    StateJson()["app_stopped"] = True
    StateJson().send_changes()
    f.shutdown_app()


@g.app.post("/new_action/")
def dst_project_selected(
    state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request),
):
    StateJson()["action_finished"] = False
    StateJson()["tag_to_remove"] = None
    StateJson()["current_step"] = 1
    StateJson()["collapsed_steps"] = {
        "input_project": False,
        "filtering": True,
        "images_table": True,
        "actions": True,
    }
    StateJson()["scrollIntoView"] = "pageTop"
    StateJson()["show_images_limit_warn"] = False
    input_project_widgets.project_selector.update_data()
    StateJson().send_changes()
    DataJson()["images_list_len"] = 0
    DataJson().send_changes()


@g.app.post("/select_tag_to_assign/")
def tag_to_assign_selected(
    state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request),
):
    if state["assign_tag_is_existing"] == "true":
        if state["tag_to_assign"] is None:
            return
        new_tag_id = state["tag_to_assign"]
        tag_data = None
        for tag in DataJson()["available_tags"]:
            if tag["id"] == new_tag_id:
                tag_data = tag
                break

        if tag_data is None:
            supervisely.logger.warn(f"Not found tag with id: {new_tag_id}")
            tag_data = DataJson()["available_tags"][0]

        StateJson()["tag_to_assign_value_type"] = tag_data["value_type"]

    if state["tag_to_assign_value_type"] == str(supervisely.TagValueType.ANY_NUMBER):
        StateJson()["tag_to_assign_value"] = 0
    elif state["tag_to_assign_value_type"] == str(supervisely.TagValueType.ANY_STRING):
        StateJson()["tag_to_assign_value"] = ""
    elif state["tag_to_assign_value_type"] == str(
        supervisely.TagValueType.ONEOF_STRING
    ):
        # TODO: bug when new tag (currently not implemented)
        StateJson()["tag_to_assign_values"] = tag_data["values"]
        StateJson()["tag_to_assign_value"] = state["tag_to_assign_values"][0]
    elif state["tag_to_assign_value_type"] == str(supervisely.TagValueType.NONE):
        StateJson()["tag_to_assign_value"] = None
    StateJson().send_changes()


@g.app.post("/select_tag_to_remove/")
def tag_to_assign_selected(
    state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request),
):
    if state["tag_to_remove"] is None:
        return
    new_tag_id = state["tag_to_remove"]
    tag_data = None
    for tag in DataJson()["available_tags"]:
        if tag["id"] == new_tag_id:
            tag_data = tag
            break

    if tag_data is None:
        supervisely.logger.warn(f"Not found tag with id: {new_tag_id}")
        return

    StateJson()["tag_to_remove_value_type"] = tag_data["value_type"]
    StateJson().send_changes()
