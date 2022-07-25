from supervisely.app import DataJson
import supervisely as sly

import src.sly_globals as g
import src.actions.widgets as card_widgets

def copy_images(ds_id):
    images_list = DataJson()['images_list']
    image_ids = {}
    for image in images_list:
        if image.dataset_id not in image_ids.keys():
            image_ids[image.dataset_id] = []
        image_ids[image.dataset_id].append(image.id)
    image_ids_len = sum([len(image_ids_per_ds) for image_ids_per_ds in image_ids.values()])
    with card_widgets.action_progress(message='Copying images...', total=image_ids_len) as pbar:
        for image_ids_per_ds in image_ids.values():
            g.api.image.copy_batch(ds_id, image_ids_per_ds, change_name_if_conflict=True, with_annotations=True, progress_cb=pbar.update)

def move_images(ds_id):
    images_list = DataJson()['images_list']
    image_ids = {}
    for image in images_list:
        if image.dataset_id not in image_ids.keys():
            image_ids[image.dataset_id] = []
        image_ids[image.dataset_id].append(image.id)
    image_ids_len = sum([len(image_ids_per_ds) for image_ids_per_ds in image_ids.values()])
    with card_widgets.action_progress(message='Moving images...', total=image_ids_len) as pbar:
        for image_ids_per_ds in image_ids.values():
            g.api.image.move_batch(ds_id, image_ids_per_ds, change_name_if_conflict=True, with_annotations=True, progress_cb=pbar.update)

def delete_images():
    images_list = DataJson()['images_list']
    image_ids = {}
    for image in images_list:
        if image.dataset_id not in image_ids.keys():
            image_ids[image.dataset_id] = []
        image_ids[image.dataset_id].append(image.id)
    image_ids_len = sum([len(image_ids_per_ds) for image_ids_per_ds in image_ids.values()])
    with card_widgets.action_progress(message='Deleting images...', total=image_ids_len) as pbar:
        for image_ids_per_ds in image_ids.values():
            g.api.image.remove_batch(image_ids_per_ds, progress_cb=pbar.update)

def assign_tag(state):
    tag = state['tag_to_add']
    tag_id = None
    if tag == '':
        raise ValueError('Specify the tag to assign!')

    project_meta_tags = g.project["project_meta"].tag_metas
    for tag_obj in project_meta_tags:
        if tag_obj.name == tag:
            tag_id = tag_obj.sly_id
            break

    if tag_id is None:
        g.project["project_meta"] = g.project["project_meta"].add_tag_meta(sly.TagMeta(tag, sly.TagValueType.NONE))
        g.api.project.update_meta(g.project["project_id"], g.project["project_meta"].to_json())

        project_meta_json = g.api.project.get_meta(g.project['project_id'])
        g.project["project_meta"] = sly.ProjectMeta.from_json(project_meta_json)
        project_meta_tags = g.project["project_meta"].tag_metas
        
        for tag_obj in project_meta_tags:
            if tag_obj.name == tag:
                tag_id = tag_obj.sly_id
                break
    
    images_list = DataJson()['images_list']
    image_ids = {}
    for image in images_list:
        if image.dataset_id not in image_ids.keys():
            image_ids[image.dataset_id] = []
        image_ids[image.dataset_id].append(image.id)
    image_ids_len = sum([len(image_ids_per_ds) for image_ids_per_ds in image_ids.values()])
    with card_widgets.action_progress(message='Assigning tag to images...', total=image_ids_len) as pbar:
        for image_ids_per_ds in image_ids.values():
            g.api.image.add_tag_batch(image_ids_per_ds, tag_id, progress_cb=pbar.update)


def remove_tags():
    images_list = DataJson()['images_list']
    image_ids = {}
    for image in images_list:
        if image.dataset_id not in image_ids.keys():
            image_ids[image.dataset_id] = []
        image_ids[image.dataset_id].append(image.id)
    image_ids_len = sum([len(image_ids_per_ds) for image_ids_per_ds in image_ids.values()])
    project_meta_tags = g.project["project_meta"].tag_metas
    project_meta_tags = [tag.sly_id for tag in project_meta_tags]
    with card_widgets.action_progress(message='Removing tag from images...', total=image_ids_len) as pbar:
        for image_ids_per_ds in image_ids.values():
            g.api.advanced.remove_tags_from_images(project_meta_tags, image_ids_per_ds, progress_cb=pbar.update)


def apply_action(state):
    action = state["selected_action"]
    res_project_info = None
    res_dataset_msg = ''
    if action == 'Copy / Move':
        project_id = None
        ds_id = None

        if state['dstProjectMode'] == 'newProject':
            project_info = g.api.project.create(g.project["workspace_id"], state["dstProjectName"], type=sly.ProjectType.IMAGES, change_name_if_conflict=True)
            project_id = project_info.id
            res_project_info = project_info
        elif state['dstProjectMode'] == 'existingProject':
            project_id = state['selectedProjectId']
            res_project_info = g.api.project.get_info_by_id(project_id)

        if state['dstDatasetMode'] == 'newDataset':
            dataset_info = g.api.dataset.create(project_id, state['dstDatasetName'])
            res_dataset_msg = f'Dataset: {dataset_info.name}'
        elif state['dstDatasetMode'] == 'existingDataset':
            dataset_info = g.api.dataset.get_info_by_name(project_id, state['selectedDatasetName'])
            res_dataset_msg = f'Dataset: {dataset_info.name}'
        ds_id = dataset_info.id

        if state["move_or_copy"] == "copy":
            copy_images(ds_id)
        elif state["move_or_copy"] == "move":
            move_images(ds_id)

    elif action == 'Delete':
        delete_images()
    elif action == 'Assign tag':
        assign_tag(state)
    elif action == 'Remove all tags':
        remove_tags()
    else:
        raise ValueError(f'Action is not supported to use: {action}')

    if action != 'Copy / Move':
        res_project_info = g.api.project.get_info_by_id(g.project['project_id'])
        if len(g.project["dataset_ids"]) == 1:
            res_dataset_msg = DataJson()['ds_names']
        elif len(g.project["dataset_ids"]) > 1:
            res_dataset_msg = f'Several datasets'
    return res_project_info, res_dataset_msg
