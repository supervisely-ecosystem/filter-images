from fastapi import Depends, HTTPException

import supervisely
from supervisely import logger

import src.input_project.widgets as card_widgets
import src.input_project.functions as card_functions

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
        card_functions.download_project(project_selector_widget=card_widgets.project_selector,
                                        state=state, project_dir=g.project_dir)

        g.project['workspace_id'] = card_widgets.project_selector.get_selected_workspace_id(state)
        g.project['project_id'] = card_widgets.project_selector.get_selected_project_id(state)
        g.project['dataset_ids'] = card_widgets.project_selector.get_selected_datasets(state)
        project_info = g.api.project.get_info_by_id(g.project['project_id'])
        state['outputProject'] = f"{project_info.name}_pipeline"

        card_functions.cache_images_info(g.project['project_id'])

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