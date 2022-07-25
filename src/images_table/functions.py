
import src.images_table.widgets as card_widgets
import src.sly_globals as g
import pandas as pd
from supervisely.app import DataJson

import supervisely


def fill_table(images_list):
    content = []
    for image_info in images_list:
        ann_tool_link = f'{g.api.server_address}/app/images/{g.TEAM_ID}/{g.WORKSPACE_ID}/{g.project["project_id"]}/{image_info.dataset_id}?page=1#image-{image_info.id}'
        content.append({
            'dataset name': g.ds_id_to_name[image_info.dataset_id],
            'item name': image_info.name,
            'image': f'<a href="{ann_tool_link}" rel="noopener noreferrer" target="_blank">open in annotaion tool<i class="zmdi zmdi-open-in-new" style="margin-left: 5px"></i></a>',
            'objects number': image_info.labels_count,
            'height': image_info.height,
            'width': image_info.width,
            'show': f'<a href="javascript:;">PREVIEW</a>'
        })
    if len(content) > 0:
        card_widgets.images_table.read_pandas(pd.DataFrame(data=[list(row.values()) for row in content],
                                                           columns=list(content[0].keys())))
    else:
        card_widgets.images_table.read_pandas(pd.DataFrame(data=[], columns=[]))


def stringify_label_tags(tags):
    final_message = ''

    for tag in tags:
        value = ''
        if tag.value is not None:
            value = f":{round(tag.value, 3)}"

        final_message += f'{tag.name}{value}<br>'

    return final_message


def show_preview(image_idx, state):
    images_list = DataJson()['images_list']
    card_widgets.images_gallery.loading = True
    card_widgets.images_gallery.clean_up()
    # TODO: bug here, check
    image = images_list[image_idx]

    state['current_item_name'] = image.name
    ann_json = g.api.annotation.download_json(image.id)
    ann = supervisely.Annotation.from_json(ann_json, g.project["project_meta"])
    img_url = image.full_storage_url

    card_widgets.images_gallery.append(
        image_url=img_url,
        title=stringify_label_tags(ann.img_tags),
        annotation=ann
    )

    card_widgets.images_gallery.loading = False