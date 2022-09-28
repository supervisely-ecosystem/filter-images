import os
from pathlib import Path

from fastapi import FastAPI, Request
from supervisely.sly_logger import logger
from starlette.staticfiles import StaticFiles

import supervisely as sly
from supervisely.app import DataJson, StateJson
from supervisely.app.fastapi import create, Jinja2Templates
from collections import OrderedDict
# from dotenv import load_dotenv # TODO: debug

app_root_directory = str(Path(__file__).parent.absolute().parents[0])
logger.info(f"App root directory: {app_root_directory}")
app_data_dir = os.path.join(app_root_directory, 'tempfiles')
app_cache_dir = os.path.join(app_data_dir, 'cache')

# TODO: for debug
# load_dotenv(os.path.join(app_root_directory, "debug.env"))
# load_dotenv(os.path.join(app_root_directory, "secret_debug.env"), override=True)

api = sly.Api.from_env()
file_cache = sly.FileCache(name="FileCache", storage_root=app_cache_dir)
app = FastAPI()
sly_app = create()

TEAM_ID = int(os.getenv('context.teamId'))
USER_ID = int(os.getenv('context.userId'))
WORKSPACE_ID = int(os.getenv('context.workspaceId'))
PROJECT_ID = int(os.getenv('modal.state.slyProjectId')) if os.getenv('modal.state.slyProjectId').isnumeric() else None

app.mount("/sly", sly_app)
app.mount("/static", StaticFiles(directory=os.path.join(app_root_directory, 'static')), name="static")
templates_env = Jinja2Templates(directory=os.path.join(app_root_directory, 'templates'))

project_dir = os.path.join(app_data_dir, 'project_dir')

project = {
    'workspace_id': None,
    'project_id': None,
    'dataset_ids': [],
    'dataset_names': [],
    'project_meta': None
}

ds_id_to_name = {}

DataJson()['steps'] = OrderedDict({
    "input_project": 1,
    "filtering": 2,
    "images_table": 3,
    "actions": 4
})
StateJson()['current_step'] = 1
StateJson()['collapsed_steps'] = {
    "input_project": False,
    "filtering": True,
    "images_table": True,
    "actions": True
}