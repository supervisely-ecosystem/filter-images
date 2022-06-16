import os

import supervisely as sly
from supervisely.app import StateJson
from supervisely.app.widgets import ProjectSelector

import src.input_project.widgets as card_widgets

import src.sly_globals as g


def cache_images_info(project_id):
    for dataset_info in g.api.dataset.get_list(project_id):
        g.images_info.extend(g.api.image.get_list(dataset_info.id))


def download_project(project_selector_widget: ProjectSelector, state: StateJson, project_dir):
    project_info = g.api.project.get_info_by_id(project_selector_widget.get_selected_project_id(state))
    pbar = card_widgets.download_project_progress(message=f'Downloading project...', total=project_info.items_count * 2)

    if os.path.exists(project_dir):
        sly.fs.clean_dir(project_dir)

    sly.download_project(g.api, project_info.id, project_dir, cache=g.file_cache,
                                 progress_cb=pbar.update, save_image_info=True, save_images=False)