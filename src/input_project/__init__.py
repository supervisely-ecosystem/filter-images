from supervisely.app import StateJson, DataJson

import src.sly_globals as g

from src.input_project.routes import *
from src.input_project.functions import *
from src.input_project.widgets import *

DataJson()['project_name'] = None
DataJson()['projectId'] = None
DataJson()['ds_names'] = []
DataJson()['projectPreviewUrl'] = None
DataJson()['instanceAddress'] = g.api.server_address

StateJson()["ds_not_selected"] = False