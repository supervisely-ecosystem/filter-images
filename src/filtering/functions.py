from supervisely.app import DataJson, StateJson
from supervisely.app.fastapi import run_sync

import src.sly_globals as g


def build_queries_from_filters(state):
    queries = []
    datasets = g.project['dataset_ids']
    filters = []
    for filter in state['selected_filters']:
        filter_data = {}
        filter_data['type'] = filter['type']
        filter_data['data'] = filter['data']
        if filter['type'] == 'images_filename' and filter['data']['value'] is None:
            filter_data['data'] = {}
        elif filter['type'] == 'objects_annotator' and filter['data']['userId'] is None:
            filter_data['data'] = {}
        elif filter['type'] == 'tagged_by_annotator' and filter['data']['userId'] is None:
            filter_data['data'] = {}
        if 'tagHasValue' in filter_data['data'].keys():
            del filter_data['data']['tagHasValue']
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
        DataJson()['available_tags'].append({
            'name': tag_obj['name'],
            'id': tag_obj['id'],
            'value_type': tag_obj['value_type'],
            'applicable_type': tag_obj['applicable_type']
        })
    run_sync(DataJson().synchronize_changes())


def get_available_annotators(team_users):
    for user in team_users:
        DataJson()['available_annotators'].append({
            'name': user.login,
            'id': user.id
        })
    run_sync(DataJson().synchronize_changes())