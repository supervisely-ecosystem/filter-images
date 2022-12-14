from fastapi import Depends, HTTPException

import supervisely
from supervisely import logger

import src.input_project.widgets as card_widgets
import src.filtering.functions as filtering_functions

from supervisely.app import DataJson, StateJson
from supervisely.app.widgets import ElementButton

import src.sly_globals as g


@card_widgets.download_project_button.add_route(app=g.app, route=ElementButton.Routes.BUTTON_CLICKED)
def download_selected_project(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    card_widgets.download_project_button.loading = True

    DataJson().send_changes()

    g.project['workspace_id'] = card_widgets.project_selector.get_selected_workspace_id(state)
    g.project['project_id'] = card_widgets.project_selector.get_selected_project_id(state)
    g.project['dataset_ids'] = card_widgets.project_selector.get_selected_datasets(state)
    DataJson()['projectId'] = g.project['project_id']
    
    # TODO: fix project selector 'AllDatasets' checkbox - can't know when checked
    # TODO: fix project selector widget: ds name instead of id
    if not g.project['dataset_ids']:
        ds_infos = g.api.dataset.get_list(g.project['project_id'])
        g.project['dataset_names'] = [dataset.name for dataset in ds_infos]   
        g.project['dataset_ids'] = [dataset.id for dataset in ds_infos]           
        DataJson()['ds_names'] = "All datasets"
    else:
        # TODO: will work when project selector will be fixed
        if not g.project['dataset_ids']:
            StateJson()["ds_not_selected"] = True
            StateJson().send_changes()
            return
        else:
            StateJson()["ds_not_selected"] = False
        # TODO: remove when fix upper will be done
        if len(g.project['dataset_ids']) > 1:
            DataJson()['ds_names'] = "Several datasets"
        elif len(g.project['dataset_ids']) == 1:
            DataJson()['ds_names'] = f'Dataset: {g.project["dataset_ids"][0]}'
        StateJson()['dstDatasetName'] = g.project['dataset_ids'][0]
        g.project['dataset_names'] = g.project['dataset_ids'].copy()
        g.project['dataset_ids'] = [g.api.dataset.get_info_by_name(g.project['project_id'], ds_name).id for ds_name in g.project['dataset_ids']]
    
    proj_info = g.api.project.get_info_by_id(g.project['project_id'])
    g.project['name'] = proj_info.name
    DataJson()['project_name'] = proj_info.name
    DataJson()['projectPreviewUrl'] = g.api.image.preview_url(proj_info.reference_image_url, 100, 100)
    StateJson()['dstProjectId'] = g.project['project_id']
    StateJson()['selectedProjectId'] = g.project['project_id']
    StateJson()['workspaceId'] = g.project['workspace_id']

    datasets = g.api.dataset.get_list(g.project['project_id'])
    g.ds_id_to_name = {dataset.id: dataset.name for dataset in datasets}
    DataJson()['available_dst_projects'] = [{"name": proj.name, "id": proj.id} for proj in g.api.project.get_list(g.project["workspace_id"])]
    DataJson()['available_dst_datasets'] = list(g.ds_id_to_name.values())

    project_meta = g.api.project.get_meta(g.project['project_id'])
    g.project['project_meta'] = supervisely.ProjectMeta.from_json(project_meta)
    team_users = g.api.user.get_team_members(g.TEAM_ID)
    
    filtering_functions.get_available_classes_and_tags(project_meta)
    filtering_functions.get_available_annotators(team_users)

    StateJson()['current_step'] += 1
    StateJson()['collapsed_steps']["filtering"] = False
    card_widgets.download_project_button.loading = False

    DataJson().send_changes()
    StateJson().send_changes()


@card_widgets.reselect_project_button.add_route(app=g.app, route=ElementButton.Routes.BUTTON_CLICKED)
def reselect_project_button_clicked(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    card_widgets.project_selector.disabled = False

    StateJson()['current_step'] = DataJson()["steps"]["input_project"]
    StateJson()['selected_filters'] = []
    StateJson()['current_preset'] = DataJson()['available_presets'][0]['name']  # All images
    StateJson().send_changes()
    DataJson()["images_list_len"] = 0
    DataJson().send_changes()