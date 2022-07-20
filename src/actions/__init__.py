from supervisely.app import StateJson, DataJson

from src.actions.routes import *
from src.actions.functions import *
from src.actions.widgets import *

DataJson()['available_actions'] = [
    'Copy to existing dataset',
    'Copy to new dataset',
    'Move to existing dataset',
    'Move to new dataset',
    'Delete',
    'Assign tag',
    'Remove all tags'
]

DataJson()['available_datasets'] = []

StateJson()['selected_dataset'] = ''
StateJson()['new_dataset'] = ''
StateJson()['selected_action'] = 'Copy to existing dataset'
StateJson()['action_process'] = False
StateJson()['tag_to_add'] = ''