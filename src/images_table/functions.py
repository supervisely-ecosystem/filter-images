import src.images_table.widgets as card_widgets
import src.sly_globals as g
import src.sly_functions as sly_functions
from supervisely.app import DataJson, StateJson

import supervisely as sly


def fill_table(images_list):
    columns = ["id", "dataset name", "item name", "image", "objects number", "show"]
    content = []
    for image_info in images_list:
        server_address = g.api.server_address.rstrip("/")
        if sly.is_development():
            url = f"{server_address}/app/images2/?datasetId={image_info.dataset_id}&imageId={image_info.id}"
        else:
            url = f"/app/images2/?datasetId={image_info.dataset_id}&imageId={image_info.id}"
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
    """Show the image with its annotation in the gallery.

    Never leaves the gallery loading: a failure is logged and shown above the preview (`preview_error`),
    and the caller (Apply filters / a table click) carries on.
    """
    gallery = card_widgets.images_gallery
    gallery.loading = True
    StateJson()["preview_error"] = ""
    try:
        gallery.clean_up()
        image_info = g.api.image.get_info_by_id(image_id, force_metadata_for_links=False)
        ann_json = g.api.annotation.download_json(image_id)
        StateJson()["current_item_name"] = image_info.name
        # The meta cached at project selection misses classes/tags created since; refreshed when needed.
        ann = sly_functions.annotation_from_json(ann_json)
        server_address = g.api.server_address.rstrip("/")
        image_path = image_info.path_original
        if sly.is_development():
            img_url = f"{server_address}/{image_path.lstrip('/')}"
        else:
            img_url = image_path

        gallery.append(image_url=img_url, title=stringify_label_tags(ann.img_tags), annotation=ann)
    except Exception as e:
        sly.logger.warning(f"Failed to show preview of image {image_id}: {e!r}", exc_info=True)
        StateJson()["preview_error"] = f"Failed to show preview of image {image_id}: {e}"
    finally:
        gallery.loading = False
