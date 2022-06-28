from fastapi import Depends, HTTPException

import supervisely
from supervisely import logger

import src.input_project.widgets as card_widgets
import src.filtering.functions as filtering_functions

from supervisely.app import DataJson
from supervisely.app.fastapi import run_sync
from supervisely.app.widgets import ElementButton

import src.sly_globals as g


@card_widgets.download_project_button.add_route(app=g.app, route=ElementButton.Routes.BUTTON_CLICKED)
def download_selected_project(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    card_widgets.download_project_button.loading = True
    card_widgets.project_selector.disabled = True

    run_sync(DataJson().synchronize_changes())

    try:
        g.project['workspace_id'] = card_widgets.project_selector.get_selected_workspace_id(state)
        g.project['project_id'] = card_widgets.project_selector.get_selected_project_id(state)
        g.project['dataset_ids'] = card_widgets.project_selector.get_selected_datasets(state)
        if not g.project['dataset_ids']:
            g.project['dataset_ids'] = [dataset.id for dataset in g.api.dataset.get_list(g.project['project_id'])]
    
        datasets = g.api.dataset.get_list(g.project['project_id'])
        g.ds_id_to_name = {dataset.id: dataset.name for dataset in datasets}
        project_meta = g.api.project.get_meta(g.project['project_id'])
        team_users = g.api.user.get_team_members(g.TEAM_ID)
        
        filtering_functions.get_available_classes_and_tags(project_meta)
        filtering_functions.get_available_annotators(team_users)

        DataJson()['current_step'] += 1
        state['collapsed_steps']["filtering"] = False
    except Exception as ex:
        card_widgets.project_selector.disabled = False

        logger.warn(f'Cannot download project: {repr(ex)}', exc_info=True)
        raise HTTPException(status_code=500, detail={'title': "Cannot download project",
                                                     'message': f'Please reselect input data and try again'})

    finally:
        card_widgets.download_project_button.loading = False
        run_sync(DataJson().synchronize_changes())
        run_sync(state.synchronize_changes())


@card_widgets.reselect_project_button.add_route(app=g.app, route=ElementButton.Routes.BUTTON_CLICKED)
def reselect_project_button_clicked(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    card_widgets.project_selector.disabled = False

    DataJson()['current_step'] = DataJson()["steps"]["input_project"]

    run_sync(DataJson().synchronize_changes())