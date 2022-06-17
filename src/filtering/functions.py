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


def remove_filter(state, idx):
    state["selected_filters"].pop(idx)
    run_sync(state.synchronize_changes())

