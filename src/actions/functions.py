from collections import defaultdict
from supervisely.app import DataJson
import supervisely as sly

import src.sly_globals as g
import src.actions.widgets as card_widgets


def group_images_by_datasets_with_new_names():
    images = defaultdict(lambda: {"images": [], "names": []})
    digits = len(str(len(g.images_list)))
    for idx, image in enumerate(g.images_list):
        images[image.dataset_id]["images"].append(image)
        new_name = f"{str(idx).zfill(digits)}_{image.name}"
        images[image.dataset_id]["names"].append(new_name)
    return images


# @sly.timeit
def copy_images(ds_ids):
    images = group_images_by_datasets_with_new_names()
    ds_mapping = None
    if g.SAVE_PROJECT_STRUCTURE:
        ds_mapping = {src_ds_id: ds_id for src_ds_id, ds_id in zip(images.keys(), ds_ids)}
    images_len = len(g.images_list)
    with card_widgets.action_progress(message="Copying images...", total=images_len) as pbar:
        for src_ds_id, images_per_ds in images.items():
            g.api.image.copy_batch_optimized(
                src_ds_id,
                images_per_ds["images"],
                ds_mapping[src_ds_id] if g.SAVE_PROJECT_STRUCTURE else ds_ids[0],
                with_annotations=True,
                progress_cb=pbar.update,
                dst_names=images_per_ds["names"],
                skip_validation=True,
                save_source_date=False,
            )
    not_empty_datasets = []
    for ds_id in ds_ids:
        dataset = g.api.dataset.get_info_by_id(ds_id)
        if dataset.images_count == 0:
            g.api.dataset.remove(ds_id)
        else:
            not_empty_datasets.append(dataset)
    return not_empty_datasets


# Old implementation for speed measurement
#
# @sly.timeit
# def copy_images(ds_id):
#     images = {}
#     for image in g.images_list:
#         if image.dataset_id not in images.keys():
#             images[image.dataset_id] = []
#         images[image.dataset_id].append(image.id)
#     images_len = sum([len(images_per_ds) for images_per_ds in images.values()])
#     with card_widgets.action_progress(message='Copying images...', total=images_len) as pbar:
#         for src_ds_id, images_per_ds in images.items():
#             g.api.image.copy_batch(ds_id, images_per_ds, change_name_if_conflict=True, with_annotations=True, progress_cb=pbar.update)


# @sly.timeit
def move_images(ds_ids):
    images = group_images_by_datasets_with_new_names()
    ds_mapping = None
    if g.SAVE_PROJECT_STRUCTURE:
        ds_mapping = {src_ds_id: ds_id for src_ds_id, ds_id in zip(images.keys(), ds_ids)}
    images_len = len(g.images_list)
    with card_widgets.action_progress(message="Moving images...", total=images_len) as pbar:
        for src_ds_id, images_per_ds in images.items():
            g.api.image.move_batch_optimized(
                src_ds_id,
                images_per_ds["images"],
                ds_mapping[src_ds_id] if g.SAVE_PROJECT_STRUCTURE else ds_ids[0],
                with_annotations=True,
                progress_cb=pbar.update,
                dst_names=images_per_ds["names"],
                skip_validation=True,
                save_source_date=False,
            )
    not_empty_datasets = []
    for ds_id in ds_ids:
        dataset = g.api.dataset.get_info_by_id(ds_id)
        if dataset.images_count == 0:
            g.api.dataset.remove(ds_id)
        else:
            not_empty_datasets.append(dataset)
    return not_empty_datasets

# Old implementation for speed measurement
#
# @sly.timeit
# def move_images(ds_id):
#     image_ids = {}
#     for image in g.images_list:
#         if image.dataset_id not in image_ids.keys():
#             image_ids[image.dataset_id] = []
#         image_ids[image.dataset_id].append(image.id)
#     image_ids_len = sum([len(image_ids_per_ds) for image_ids_per_ds in image_ids.values()])
#     with card_widgets.action_progress(message='Moving images...', total=image_ids_len) as pbar:
#         for image_ids_per_ds in image_ids.values():
#             g.api.image.move_batch(ds_id, image_ids_per_ds, change_name_if_conflict=True, with_annotations=True, progress_cb=pbar.update)


def delete_images():
    image_ids = {}
    for image in g.images_list:
        if image.dataset_id not in image_ids.keys():
            image_ids[image.dataset_id] = []
        image_ids[image.dataset_id].append(image.id)
    image_ids_len = sum(
        [len(image_ids_per_ds) for image_ids_per_ds in image_ids.values()]
    )
    with card_widgets.action_progress(
        message="Deleting images...", total=image_ids_len
    ) as pbar:
        for image_ids_per_ds in image_ids.values():
            g.api.image.remove_batch(
                image_ids_per_ds, progress_cb=pbar.update, batch_size=500
            )


def assign_tag(state):
    tag_value = state["tag_to_assign_value"]
    if state["assign_tag_is_existing"] == "true":
        if state["tag_to_assign"] is None:
            raise ValueError("Select existing tag to assign value!")
        tag_id = state["tag_to_assign"]
    else:
        if state["tag_to_assign_name"] == "":
            raise ValueError("Tag name can't be empty!")
        possible_values = None

        # TODO: currently is not supported
        if state["tag_to_assign_value_type"] == str(sly.TagValueType.ONEOF_STRING):
            possible_values = state["tag_to_assign_values"]

        new_tag_meta = sly.TagMeta(
            state["tag_to_assign_name"],
            state["tag_to_assign_value_type"],
            possible_values=possible_values,
            applicable_to=state["tag_to_assign_applicable_to"],
        )
        g.project["project_meta"] = g.project["project_meta"].add_tag_meta(new_tag_meta)
        g.api.project.update_meta(
            g.project["project_id"], g.project["project_meta"].to_json()
        )

        project_meta_json = g.api.project.get_meta(g.project["project_id"])
        g.project["project_meta"] = sly.ProjectMeta.from_json(project_meta_json)
        project_meta_tags = g.project["project_meta"].tag_metas

        for tag_obj in project_meta_tags:
            if tag_obj.name == state["tag_to_assign_name"]:
                tag_id = tag_obj.sly_id
                break

    image_ids = {}
    for image in g.images_list:
        if image.dataset_id not in image_ids.keys():
            image_ids[image.dataset_id] = []
        image_ids[image.dataset_id].append(image.id)
    image_ids_len = sum(
        [len(image_ids_per_ds) for image_ids_per_ds in image_ids.values()]
    )
    with card_widgets.action_progress(
        message="Assigning tag to images...", total=image_ids_len
    ) as pbar:
        for image_ids_per_ds in image_ids.values():
            g.api.image.add_tag_batch(
                image_ids_per_ds, tag_id, tag_value, progress_cb=pbar.update
            )


def remove_tags_from_images():
    image_ids = {}
    for image in g.images_list:
        if image.dataset_id not in image_ids.keys():
            image_ids[image.dataset_id] = []
        image_ids[image.dataset_id].append(image.id)
    image_ids_len = sum(
        [len(image_ids_per_ds) for image_ids_per_ds in image_ids.values()]
    )
    project_meta_tags = g.project["project_meta"].tag_metas
    project_meta_tags = [tag.sly_id for tag in project_meta_tags]
    with card_widgets.action_progress(
        message="Removing all tags from images...", total=image_ids_len
    ) as pbar:
        for image_ids_per_ds in image_ids.values():
            g.api.advanced.remove_tags_from_images(
                project_meta_tags, image_ids_per_ds, progress_cb=pbar.update
            )


def remove_specific_tag_from_images(state):
    if state["tag_to_remove"] is None:
        raise ValueError("Select tag to remove!")
    tag_id = state["tag_to_remove"]
    image_ids = {}
    for image in g.images_list:
        if image.dataset_id not in image_ids.keys():
            image_ids[image.dataset_id] = []
        image_ids[image.dataset_id].append(image.id)
    image_ids_len = sum(
        [len(image_ids_per_ds) for image_ids_per_ds in image_ids.values()]
    )
    project_meta_tags = g.project["project_meta"].tag_metas
    project_meta_tags = [tag.sly_id for tag in project_meta_tags]
    if not tag_id in project_meta_tags:
        raise ValueError("Tag is not found in project!")
    with card_widgets.action_progress(
        message="Removing specifiid tag from images...", total=image_ids_len
    ) as pbar:
        for image_ids_per_ds in image_ids.values():
            g.api.advanced.remove_tags_from_images(
                [tag_id], image_ids_per_ds, progress_cb=pbar.update
            )
    state["tag_to_remove"] = None

def data_to_readable_format(data):
    data_to_display = "<div><b>Data:</b></div>\n"
    for field, field_data in data.items():
        if field == "tagId":
            for tag_dict in DataJson()["available_tags"]:
                if field_data == tag_dict["id"]:
                    data_to_display += f'<div>tag: {tag_dict["name"]}</div>\n'
        elif field == "tagClassId":
            for class_dict in DataJson()["available_classes"]:
                if field_data == class_dict["id"]:
                    data_to_display += f'<div>class: {class_dict["name"]}</div>\n'
        elif field == "classId":
            for class_dict in DataJson()["available_classes"]:
                if field_data == class_dict["id"]:
                    data_to_display += f'<div>class: {class_dict["name"]}</div>\n'
        elif field == "userId":
            for user_dict in DataJson()["available_annotators"]:
                if field_data == user_dict["id"]:
                    data_to_display += f'<div>annotator: {user_dict["name"]}</div>\n'
        elif field == "status":
            for status_dict in DataJson()["issue_statuses"]:
                if field_data == status_dict["value"]:
                    data_to_display += f'<div>status: {status_dict["name"]}</div>\n'
        elif field == "from":
            data_to_display += f"<div>countFrom: {field_data}</div>\n"
        elif field == "to":
            data_to_display += f"<div>countTo: {field_data}</div>\n"
        else:
            data_to_display += f"<div>{field}: {str(field_data)}</div>\n"
    return data_to_display


def add_metadata_to_project_readme(res_project_info, dataset_infos, action, state):
    current_readme = res_project_info.readme
    new_readme_text = "### Project changed by Filter Images app:\n"
    if res_project_info.id == g.project["project_id"]:
        new_readme_text += "<div><b>Source project name:</b> the same.</div>\n"
        new_readme_text += "<div><b>Source project ID:</b> the same.</div>\n"
    else:
        new_readme_text += (
            f'<div><b>Source project name:</b> {g.project["name"]}</div>\n'
        )
        new_readme_text += (
            f'<div><b>Source project ID:</b> {g.project["project_id"]}</div>\n'
        )

    new_readme_text += (
        f'<div><b>Source dataset names:</b> {g.project["dataset_names"]}</div>\n'
    )
    new_readme_text += (
        f'<div><b>Source dataset IDs:</b> {g.project["dataset_ids"]}</div>\n'
    )

    if action != "Copy / Move":
        new_readme_text += f"<div><b>Applied action:</b> {action.lower()}</div>\n"
    else:
        new_readme_text += f'<div><b>Applied action:</b> {state["move_or_copy"].lower()}</div>\n'
    if dataset_infos is not None:
        new_readme_text += f"<div><b>Destination datasets names:</b> {[ds.name for ds in dataset_infos]}</div>\n"
        new_readme_text += f"<div><b>Destination datasets IDs:</b> {[ds.id for ds in dataset_infos]}</div>\n"
    else:
        new_readme_text += f"<div><b>Destination datasets:</b> Unknown</div>\n"

    new_readme_text += f"### Applied filters:\n"
    if not state["selected_filters"]:
        new_readme_text += f"<div><b>Name:</b> All images</div>\n"
    else:
        for filter_idx, filter in enumerate(state["selected_filters"]):
            new_readme_text += (
                f'<div><b>{filter_idx + 1}. Name:</b> {filter["name"]}</div>\n'
            )
            new_readme_text += f'<div><b>Filter type:</b> {filter["type"]}</div>\n'
            data = data_to_readable_format(filter["data"])
            new_readme_text += data

    new_readme_text += "<hr />\n"
    readme_text = current_readme + "\n" + new_readme_text
    g.api.project.edit_info(res_project_info.id, readme=readme_text)


def apply_action(state):
    action = state["selected_action"]
    res_project_info = None
    res_dataset_msg = ""
    if action == "Copy / Move":
        project_id = None
        ds_ids = None
        g.SAVE_PROJECT_STRUCTURE = False

        if state["dstProjectMode"] == "newProject":
            project_name = state["dstProjectName"]
            if project_name == "":
                sly.logger.info(f"Project name is not specified. Using default name.")
                project_name = g.DEFAULT_PROJECT_NAME
            project_info = g.api.project.create(
                g.project["workspace_id"],
                project_name,
                type=sly.ProjectType.IMAGES,
                change_name_if_conflict=True,
            )
            sly.logger.info(f"Project {project_info.name} has been created.")
            project_id = project_info.id
            res_project_info = project_info
        elif state["dstProjectMode"] == "existingProject":
            project_id = state["selectedProjectId"]
            res_project_info = g.api.project.get_info_by_id(project_id)

        if state["dstDatasetMode"] == "newDataset":
            if state["dstDatasetName"] == "":
                raise ValueError("Dataset name can't be empty!")
            dataset_infos = [
                g.api.dataset.create(
                    project_id, state["dstDatasetName"], change_name_if_conflict=True
                )
            ]
        elif state["dstDatasetMode"] == "similarDatasets":
            g.SAVE_PROJECT_STRUCTURE = True
            existing_dataset_infos = g.api.dataset.get_list(g.PROJECT_ID)
            existing_dataset_names = [dataset_info.name for dataset_info in existing_dataset_infos]
            dataset_infos = []
            for name in existing_dataset_names:
                new_ds = g.api.dataset.create(project_id, name, change_name_if_conflict=True)
                dataset_infos.append(new_ds)

        elif state["dstDatasetMode"] == "existingDataset":
            dataset_infos = [
                g.api.dataset.get_info_by_name(project_id, state["selectedDatasetName"])
            ]
        ds_ids = [ds_info.id for ds_info in dataset_infos]

        if state["move_or_copy"] == "copy":
            dataset_infos = copy_images(ds_ids)
        elif state["move_or_copy"] == "move":
            dataset_infos = move_images(ds_ids)

    elif action == "Delete":
        delete_images()
    elif action == "Assign tag":
        assign_tag(state)
    elif action == "Remove all tags (from images)":
        remove_tags_from_images()
    elif action == "Remove specific tag (from images)":
        remove_specific_tag_from_images(state)
    else:
        raise ValueError(f"Action is not supported to use: {action}")

    if action == "Copy / Move":
        if len(dataset_infos) == 1:
            res_dataset_msg = f"Dataset: {dataset_infos[0].name}"
        else:
            res_dataset_msg = f"Datasets: {[ds_info.name for ds_info in dataset_infos]}"
    else:
        dataset_infos = None
        res_project_info = g.api.project.get_info_by_id(g.project["project_id"])
        if len(g.project["dataset_ids"]) == 1:
            res_dataset_msg = DataJson()["ds_names"]
        elif len(g.project["dataset_ids"]) > 1:
            res_dataset_msg = "Several datasets"

    add_metadata_to_project_readme(res_project_info, dataset_infos, action, state)

    return res_project_info, res_dataset_msg
