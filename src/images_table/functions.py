
import src.images_table.widgets as card_widgets
import src.sly_globals as g
from supervisely.app import DataJson
from supervisely.app.fastapi import run_sync

import supervisely


def fill_table(images_list):
    columns = [
        'id',
        'dataset name',
        'item name',
        'image',
        'objects number',
        'height',
        'width',
        'show'
    ]
    content = []
    for image_info in images_list:
        ann_tool_link = f'{g.api.server_address}/app/images/{g.TEAM_ID}/{g.WORKSPACE_ID}/{g.project["project_id"]}/{image_info.dataset_id}?page=1#image-{image_info.id}'
        content.append([
            image_info.id,
            g.ds_id_to_name[image_info.dataset_id],
            image_info.name,
            f'<a href="{ann_tool_link}" rel="noopener noreferrer" target="_blank">open in annotaion tool<i class="zmdi zmdi-open-in-new" style="margin-left: 5px"></i></a>',
            image_info.labels_count,
            image_info.height,
            image_info.width,
            f'<a href="javascript:;">PREVIEW</a>'
        ])
    if len(content) > 0:
        card_widgets.images_table.read_json({'data': content, 'columns': columns})
    else:
        card_widgets.images_table.read_json({'data':[], 'columns':[]})


def stringify_label_tags(tags):
    final_message = ''

    for tag in tags:
        value = ''
        if tag.value is not None:
            value = f":{round(tag.value, 3)}"

        final_message += f'{tag.name}{value}<br>'

    return final_message


def show_preview(image_id, state):
    card_widgets.images_gallery.loading = True
    card_widgets.images_gallery.clean_up()

    image_info = g.api.image.get_info_by_id(image_id)
    ann_json = g.api.annotation.download_json(image_id)
    state['current_item_name'] = image_info.name
    ann = supervisely.Annotation.from_json(ann_json, g.project["project_meta"])
    img_url = image_info.full_storage_url

    card_widgets.images_gallery.append(
        image_url=img_url,
        title=stringify_label_tags(ann.img_tags),
        annotation=ann
    )

    card_widgets.images_gallery.loading = False