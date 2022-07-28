from supervisely.app import StateJson, DataJson

from src.filtering.routes import *
from src.filtering.functions import *
from src.filtering.widgets import *


DataJson()['available_classes'] = [{
    'name': 'Any class',
    'id': None
}]
DataJson()['available_annotators'] = [{
    'name': 'Any annotator',
    'id': None
}]
DataJson()['available_tags'] = [{
    'name': 'Any tag',
    'id': None
}]

DataJson()['issue_statuses'] = [
    {
        "name": "All",
        "value": None
    },
    {
        "name": "Open",
        "value": "open"
    },
    {
        "name": "Closed",
        "value": "closed"
    }
]

DataJson()['available_filters'] = [
    {   
        "name": "By Filename",
        "type": "images_filename",
        "data": {
            "value": None
        }
    },
    {
        "name": "With tag",
        "type": "images_tag",
        "data": {
            "tagId": None,
            "include": True,
            "value": None,
            "valueType": None
        }
    },
    {
        "name": "Without tag",
        "type": "images_tag",
        "data": {
            "tagId": None,
            "include": False,
            "value": None,
            "valueType": None
        }
    },
    {
        "name": "Objects with tag",
        "type": "objects_tag",
        "data": {
            "from": 1,
            "to": 9999,
            "tagClassId": None,
            "tagId": None,
            "include": True,
            "value": None,
            "valueType": None
        }
    },
    {
        "name": "Objects without tag",
        "type": "objects_tag",
        "data": {
            "from": 1,
            "to": 9999,
            "tagClassId": None,
            "tagId": None,
            "include": False,
            "value": None,
            "valueType": None
        }
    },
    {
        "name": "Objects of class",
        "type": "objects_class",
        "data": {
            "from": 1,
            "to": 9999,
            "classId": None
        }
    },
    {
        "name": "Objects by annotator",
        "type": "objects_annotator",
        "data": {
            "from": 1,
            "to": 9999,
            "userId": None
        }
    },
    {
        "name": "Tagged by annotator",
        "type": "tagged_by_annotator",
        "data": {
            "from": 1,
            "to": 9999,
            "userId": None
        }
    },
    {
        "name": "With issues",
        "type": "issues_count",
        "data": {
            "from": 1,
            "to": 9999,
            "status": None
        }
    },
]

DataJson()['default_filter'] = DataJson()['available_filters'][0] # by filename

DataJson()['available_presets'] = [
    {
        "name": "All images",
        "filters": []
    },
    {
        "name": "With one object or more",
        "filters": [ 
            DataJson()['available_filters'][5] # objects of class
        ]
    },
    {
        "name": "Without any objects",
        "filters": [
            {
                "name": "Objects of class",
                "type": "objects_class",
                "data": {
                    "from": 0,
                    "to": 0,
                    "classId": None
                }
            }
        ]
    },
    {
        "name": "Labeled by me",
        "filters": [
            {
                "name": "Objects by annotator",
                "type": "objects_annotator",
                "data": {
                    "from": 1,
                    "to": 9999,
                    "userId": g.USER_ID
                }
            }
        ]
    },
    {
        "name": "Has issues",
        "filters": [
            {
                "name": "With issues",
                "type": "issues_count",
                "data": {
                    "from": 1,
                    "to": 9999,
                    "status": "open"
                }
            }
        ]
    }
]

StateJson()['current_preset'] = DataJson()['available_presets'][0]["name"] # all images

StateJson()['selected_filters'] = []
StateJson()['objects_count_buttons_visible'] = []
StateJson()['filter_to_change'] = None
StateJson()['filtering'] = False
StateJson()['empty_list'] = False
StateJson()['available_tag_values'] = []

DataJson()['images_list'] = []
