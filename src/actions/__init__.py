from supervisely.app import StateJson, DataJson

from src.actions.routes import *
from src.actions.functions import *
from src.actions.widgets import *

DataJson()["available_actions"] = [
    "Copy / Move",
    "Delete",
    "Assign tag",
    "Remove all tags (from images)",
    "Remove specific tag (from images)",
]

StateJson()["selected_action"] = "Copy / Move"
StateJson()["action_process"] = False
StateJson()["loadingDatasets"] = False
StateJson()["action_finished"] = False
StateJson()["apply_text"] = "APPLY"

StateJson()["dstProjectMode"] = "newProject"  # ['newProject', 'existingProject']
StateJson()["dstDatasetMode"] = "newDataset"  # ['newDataset', 'similarDatasets', 'existingDataset']
StateJson()["move_or_copy"] = "copy"
StateJson()["dstDatasetName"] = ""
StateJson()["dstProjectName"] = ""
StateJson()["selectedDatasetName"] = None
StateJson()["selectedProjectId"] = None
StateJson()["workspaceId"] = None

DataJson()["dstProjectId"] = None
DataJson()["dstProjectPreviewUrl"] = None
DataJson()["dstDatasetMsg"] = ""
DataJson()["available_dst_projects"] = []
DataJson()["available_dst_datasets"] = []

StateJson()["tag_applicable_to_values"] = [
    {"name": "Images and objects", "value": "all"},
    {"name": "Images only", "value": "imagesOnly"},
]

StateJson()["tag_value_types"] = [
    {"name": "None", "value": "none"},
    {"name": "Number", "value": "any_number"},
    {"name": "Text", "value": "any_string"},
    {"name": "One of", "value": "oneof_string"},
]

StateJson()["tag_to_assign_name"] = ""
StateJson()["assign_tag_is_existing"] = "false"
StateJson()["tag_to_assign_applicable_to"] = StateJson()["tag_applicable_to_values"][0]["value"]
StateJson()["tag_to_assign"] = None
StateJson()["tag_to_assign_value_type"] = StateJson()["tag_value_types"][0]["value"]
StateJson()["tag_to_assign_value"] = None
StateJson()["tag_to_assign_values"] = []
StateJson()["tag_to_remove"] = None
StateJson()["tag_to_remove_value_type"] = None
