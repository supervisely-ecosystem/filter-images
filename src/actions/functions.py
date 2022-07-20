from supervisely.annotation.tag_meta_collection import TagMetaCollection
from supervisely.app import DataJson, StateJson
from supervisely.app.fastapi import run_sync
import supervisely as sly

import src.sly_globals as g
import src.filtering.widgets as card_widgets

def copy_images(ds_id):
    images_list = DataJson()['images_list']
    image_ids = [image.id for image in images_list]
    g.api.image.copy_batch(ds_id, image_ids, change_name_if_conflict=True, with_annotations=True)

def move_images(ds_id):
    images_list = DataJson()['images_list']
    image_ids = [image.id for image in images_list]
    g.api.image.move_batch(ds_id, image_ids, change_name_if_conflict=True, with_annotations=True)

def delete_images():
    # TODO: Fix "Can't remove last image in dataset" or forbid deletion of all elements
    images_list = DataJson()['images_list']
    image_ids = [image.id for image in images_list]
    g.api.image.remove_batch(image_ids)

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
    image_ids = [image.id for image in images_list]
    g.api.image.add_tag_batch(image_ids, tag_id)


def remove_tags():
    images_list = DataJson()['images_list']
    image_ids = [image.id for image in images_list]
    project_meta_tags = g.project["project_meta"].tag_metas
    project_meta_tags = [tag.sly_id for tag in project_meta_tags]
    g.api.advanced.remove_tags_from_images(project_meta_tags, image_ids)


def apply_action(state):
    action = state["selected_action"]
    if action == 'Copy to existing dataset':
        dataset = g.api.dataset.get_info_by_name(g.project["project_id"], state["selected_dataset"])
        copy_images(dataset.id)
    elif action == 'Copy to new dataset':
        dataset = g.api.dataset.create(g.project["project_id"], state["new_dataset"])
        copy_images(dataset.id)
    elif action == 'Move to existing dataset':
        dataset = g.api.dataset.get_info_by_name(g.project["project_id"], state["selected_dataset"])
        move_images(dataset.id)
    elif action == 'Move to new dataset':
        dataset = g.api.dataset.create(g.project["project_id"], state["new_dataset"])
        move_images(dataset.id)
    elif action == 'Delete':
        delete_images()
    elif action == 'Assign tag':
        assign_tag(state)
    elif action == 'Remove all tags':
        remove_tags()
    else:
        raise ValueError(f'Action is not supported to use: {action}')
