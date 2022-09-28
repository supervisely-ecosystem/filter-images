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
    tag_value = state['tag_to_assign_value']
    if state['assign_tag_is_existing'] == 'true':
        if state['tag_to_assign'] is None:
            raise ValueError("Select existing tag to assign value!")
        tag_id = state['tag_to_assign']
    else:
        if state['tag_to_assign_name'] == '':
            raise ValueError("Tag name can't be empty!")
        possible_values = None

        # TODO: currently is not supported
        if state['tag_to_assign_value_type'] == str(sly.TagValueType.ONEOF_STRING):
            possible_values = state['tag_to_assign_values']
    
        new_tag_meta = sly.TagMeta(
            state['tag_to_assign_name'], 
            state['tag_to_assign_value_type'], 
            possible_values=possible_values, 
            applicable_to=state['tag_to_assign_applicable_to'])
        g.project["project_meta"] = g.project["project_meta"].add_tag_meta(new_tag_meta)
        g.api.project.update_meta(g.project["project_id"], g.project["project_meta"].to_json())

        project_meta_json = g.api.project.get_meta(g.project['project_id'])
        g.project["project_meta"] = sly.ProjectMeta.from_json(project_meta_json)
        project_meta_tags = g.project["project_meta"].tag_metas
        
        for tag_obj in project_meta_tags:
            if tag_obj.name == state['tag_to_assign_name']:
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
            g.api.image.add_tag_batch(image_ids_per_ds, tag_id, tag_value, progress_cb=pbar.update)


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
    with card_widgets.action_progress(message='Removing tags from images...', total=image_ids_len) as pbar:
        for image_ids_per_ds in image_ids.values():
            g.api.advanced.remove_tags_from_images(project_meta_tags, image_ids_per_ds, progress_cb=pbar.update)


def add_metadata_to_project_readme(res_project_info, dataset_info, action, state):
    current_readme = res_project_info.readme
    new_readme_text = '### Project changed by Filter Images app:\n'
    if res_project_info.id == g.project['project_id']:
        new_readme_text += '<div><b>Source project name:</b> the same.</div>\n'
        new_readme_text += '<div><b>Source project ID:</b> the same.</div>\n'
    else:
        new_readme_text += f'<div><b>Source project name:</b> {g.project["name"]}</div>\n'
        new_readme_text += f'<div><b>Source project ID:</b> {g.project["project_id"]}</div>\n'

    new_readme_text += f'<div><b>Source dataset names:</b> {g.project["dataset_names"]}</div>\n'
    new_readme_text += f'<div><b>Source dataset IDs:</b> {g.project["dataset_ids"]}</div>\n'

    if action != 'Copy / Move':
        new_readme_text += f'<div><b>Applied action:</b> {action.lower()}</div>\n'
    else:
        new_readme_text += f'<div><b>Applied action:</b> {state["move_or_copy"].lower()}</div>\n'
    if dataset_info is not None:
        new_readme_text += f'<div><b>Destination dataset name:</b> {dataset_info.name}</div>\n'
        new_readme_text += f'<div><b>Destination dataset ID:</b> {dataset_info.id}</div>\n'
    else:
        new_readme_text += f'<div><b>Destination datasets:</b> Unknown</div>\n'
    
    new_readme_text += f'### Applied filters:\n'
    if not state['selected_filters']:
        new_readme_text += f'<div><b>Name:</b> All images</div>\n'
    else:
        for filter_idx, filter in enumerate(state['selected_filters']):
            new_readme_text += f'<div><b>{filter_idx + 1}. Name:</b> {filter["name"]}</div>\n'
            new_readme_text += f'<div><b>Filter type:</b> {filter["type"]}</div>\n'
            new_readme_text += f'<div><b>Data:</b> {filter["data"]}</div>\n'


    new_readme_text += '<hr />\n'
    readme_text = current_readme + new_readme_text
    g.api.project.edit_info(res_project_info.id, readme=readme_text)


def apply_action(state):
    action = state["selected_action"]
    res_project_info = None
    res_dataset_msg = ''
    if action == 'Copy / Move':
        project_id = None
        ds_id = None

        if state['dstProjectMode'] == 'newProject':
            if state["dstProjectName"] == '':
                raise ValueError("Project name can't be empty!")
            project_info = g.api.project.create(g.project["workspace_id"], state["dstProjectName"], type=sly.ProjectType.IMAGES, change_name_if_conflict=True)
            project_id = project_info.id
            res_project_info = project_info
        elif state['dstProjectMode'] == 'existingProject':
            project_id = state['selectedProjectId']
            res_project_info = g.api.project.get_info_by_id(project_id)

        if state['dstDatasetMode'] == 'newDataset':
            if state["dstDatasetName"] == '':
                raise ValueError("Dataset name can't be empty!")
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
        dataset_info = None
        res_project_info = g.api.project.get_info_by_id(g.project['project_id'])
        if len(g.project["dataset_ids"]) == 1:
            res_dataset_msg = DataJson()['ds_names']
        elif len(g.project["dataset_ids"]) > 1:
            res_dataset_msg = 'Several datasets'
    
    add_metadata_to_project_readme(res_project_info, dataset_info, action, state)

    return res_project_info, res_dataset_msg
