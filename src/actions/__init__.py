from supervisely.app import StateJson, DataJson

from src.actions.routes import *
from src.actions.functions import *
from src.actions.widgets import *

DataJson()['available_actions'] = [
    'Copy / Move',
    'Delete',
    'Assign tag',
    'Remove all tags'
]

StateJson()['selected_action'] = 'Copy / Move'
StateJson()['action_process'] = False
StateJson()['tag_to_add'] = ''
StateJson()['loadingDatasets'] = False
StateJson()['action_finished'] = False

StateJson()['dstProjectMode'] = 'newProject' # ['newProject', 'existingProject']
StateJson()['dstDatasetMode'] = 'newDataset' # ['newDataset', 'existingDataset']
StateJson()['move_or_copy'] = 'copy'
StateJson()['dstDatasetName'] = None
StateJson()['dstProjectName'] = None
StateJson()['selectedDatasetName'] = None
StateJson()['selectedProjectId'] = None
StateJson()['workspaceId'] = None

DataJson()['dstProjectId'] = None
DataJson()['dstProjectPreviewUrl'] = None
DataJson()['dstDatasetMsg'] = ''
DataJson()['available_dst_projects'] = []
DataJson()['available_dst_datasets'] = []