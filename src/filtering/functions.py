from supervisely.app import DataJson, StateJson
from supervisely.app.fastapi import run_sync

def build_query_from_filters():
    query = {}
    return query

def get_images(query):
    images_list = []
    return images_list

def fill_table(images_list):
    content = {}
    return content

def show_preview():
    pass

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
