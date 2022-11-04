from supervisely.app import StateJson

from src.images_table.routes import *
from src.images_table.functions import *
from src.images_table.widgets import *

StateJson()['current_item_name'] = ''
StateJson()['loading_preview'] = False
StateJson()['show_images_limit_warn'] = False
DataJson()["table_images_limit"] = g.TABLE_IMAGES_LIMIT