import src.images_table.widgets as card_widgets
import src.sly_globals as g
from supervisely.app import DataJson, StateJson

import supervisely as sly


def fill_table(images_list):
    columns = ["id", "dataset name", "item name", "image", "objects number", "show"]
    content = []
    for image_info in images_list:
        server_address = g.api.server_address.rstrip("/")
        url = f"{server_address}/app/images2/?datasetId={image_info.dataset_id}&imageId={image_info.id}"
        text = "open in annotaion tool"
        icon = "<i class='zmdi zmdi-open-in-new' style='margin-left: 5px'></i>"
        link = f'<a href="{url}" rel="noopener noreferrer" target="_blank">{text}{icon}</a>'
        content.append(
            [
                image_info.id,
                g.ds_id_to_name[image_info.dataset_id],
                image_info.name,
                link,
                image_info.labels_count,
                f'<a href="javascript:;">PREVIEW</a>',
            ]
        )
    if len(content) > 0:
        card_widgets.images_table.read_json({"data": content, "columns": columns})
    else:
        card_widgets.images_table.read_json({"data": [], "columns": []})


def stringify_label_tags(tags):
    final_message = ""

    for tag in tags:
        value = ""
        if tag.value is not None:
            if tag.meta.value_type == str(sly.TagValueType.ANY_NUMBER):
                value = f":{round(tag.value, 3)}"
            else:
                value = f":{tag.value}"

        final_message += f"{tag.name}{value}<br>"

    return final_message


def show_preview(image_id):
    card_widgets.images_gallery.loading = True
    card_widgets.images_gallery.clean_up()

    image_info = g.api.image.get_info_by_id(image_id, force_metadata_for_links=False)
    ann_json = g.api.annotation.download_json(image_id)
    StateJson()["current_item_name"] = image_info.name
    ann = sly.Annotation.from_json(ann_json, g.project["project_meta"])
    server_address = g.api.server_address.rstrip("/")
    image_path = image_info.path_original.lstrip("/")
    img_url = f"{server_address}/{image_path}"

    card_widgets.images_gallery.append(
        image_url=img_url, title=stringify_label_tags(ann.img_tags), annotation=ann
    )

    card_widgets.images_gallery.loading = False
