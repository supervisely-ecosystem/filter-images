
import src.images_table.widgets as card_widgets
import src.sly_globals as g
import pandas as pd
from supervisely.app import DataJson

import supervisely


def fill_table(images_list):
    content = []
    for image_info in images_list:
        content.append({
            'dataset name': g.ds_id_to_name[image_info.dataset_id],
            'item name': image_info.name,
            'image': f'<a href="{image_info.full_storage_url}" rel="noopener noreferrer" target="_blank">open <i class="zmdi zmdi-open-in-new" style="margin-left: 5px"></i></a>',
            'objects number': image_info.labels_count,
            'height': image_info.height,
            'width': image_info.width
        })
    if len(content) > 0:
        card_widgets.images_table.read_pandas(pd.DataFrame(data=[list(row.values()) for row in content],
                                                           columns=list(content[0].keys())))
    else:
        card_widgets.images_table.read_pandas(pd.DataFrame(data=[], columns=[]))


def show_preview(image_idx):
    images_list = DataJson()['images_list']
    card_widgets.images_gallery.loading = True
    card_widgets.images_gallery.clean_up()
    image = images_list[image_idx]

    ann_json = g.api.annotation.download_json(image.id)
    ann = supervisely.Annotation.from_json(ann_json, g.project["project_meta"])
    img_url = image.full_storage_url

    card_widgets.images_gallery.append(
        image_url=img_url,
        title=image.name,
        annotation=ann
    )

    card_widgets.images_gallery.loading = False