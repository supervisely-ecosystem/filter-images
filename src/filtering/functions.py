import supervisely
from supervisely.app import DataJson, StateJson
from supervisely.app.fastapi import run_sync

import src.sly_globals as g
import copy


def build_queries_from_filters(state):
    queries = []
    datasets = g.project['dataset_ids']
    filters = []
    for filter in state['selected_filters']:
        filter_data = {}
        filter_data['type'] = filter['type']
        filter_data['data'] = copy.deepcopy(filter['data'])
        if filter['type'] == 'images_filename' and filter['data']['value'] is None:
            filter_data['data'] = {}
        elif filter['type'] == 'objects_annotator' and filter['data']['userId'] is None:
            filter_data['data'] = {}
        elif filter['type'] == 'tagged_by_annotator' and filter['data']['userId'] is None:
            filter_data['data'] = {}
        if 'valueType' in filter_data['data'].keys():
            if filter_data['data']['valueType'] == str(supervisely.TagValueType.ANY_NUMBER):
                filter_data['data']['value']['from'] = str(filter_data['data']['value']['from'])
                filter_data['data']['value']['to'] = str(filter_data['data']['value']['to'])
            elif filter_data['data']['valueType'] == str(supervisely.TagValueType.ANY_STRING):
                assert filter_data['data']['value'] != '', "Tag value can't be empty."
            del filter_data['data']['valueType']
        filters.append(filter_data)
    for dataset in datasets:
        queries.append({
            'datasetId': dataset,
            'filters': filters
        })

    return queries


def get_images(queries):
    images_list = []
    for query in queries:
        ds_images = g.api.image.get_filtered_list(query["datasetId"], query["filters"])
        images_list.extend(ds_images)

    return images_list


def get_available_classes_and_tags(project_meta):
    for class_obj in project_meta["classes"]:
        DataJson()['available_classes'].append({
            'name': class_obj['title'],
            'id': class_obj['id']
        })
    for tag_obj in project_meta["tags"]:
        tag_dict = {
            'name': tag_obj['name'],
            'id': tag_obj['id'],
            'value_type': tag_obj['value_type'],
            'applicable_type': tag_obj['applicable_type']
        }
        if "values" in tag_obj.keys():
            tag_dict["values"] = tag_obj["values"]
        DataJson()['available_tags'].append(tag_dict)
    run_sync(DataJson().synchronize_changes())


def get_available_annotators(team_users):
    for user in team_users:
        DataJson()['available_annotators'].append({
            'name': user.login,
            'id': user.id
        })
    run_sync(DataJson().synchronize_changes())
