import os
from pathlib import Path

from fastapi import FastAPI, Request
from supervisely.sly_logger import logger
from starlette.staticfiles import StaticFiles

import supervisely as sly
from supervisely.app import DataJson, StateJson
from supervisely.app.fastapi import create, Jinja2Templates
from collections import OrderedDict


app_root_directory = str(Path(__file__).parent.absolute().parents[0])
logger.info(f"App root directory: {app_root_directory}")
app_data_dir = os.path.join(app_root_directory, "tempfiles")
app_cache_dir = os.path.join(app_data_dir, "cache")

# TODO: debug
from dotenv import load_dotenv

if sly.is_development():
    load_dotenv(os.path.join(app_root_directory, "local.env"))
    load_dotenv(os.path.expanduser("~/supervisely.env"))

api = sly.Api.from_env()
file_cache = sly.FileCache(name="FileCache", storage_root=app_cache_dir)
app = FastAPI()
sly_app = create()

TEAM_ID = sly.env.team_id()
USER_ID = sly.env.user_id()
WORKSPACE_ID = sly.env.workspace_id()
PROJECT_ID = sly.env.project_id()
DEFAULT_PROJECT_NAME = "New filtered project"
SAVE_PROJECT_STRUCTURE = False

app.mount("/sly", sly_app)
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(app_root_directory, "static")),
    name="static",
)
templates_env = Jinja2Templates(directory=os.path.join(app_root_directory, "templates"))

project_dir = os.path.join(app_data_dir, "project_dir")

project = {
    "workspace_id": None,
    "project_id": None,
    "name": None,
    "dataset_ids": [],
    "dataset_names": [],
    "project_meta": None,
}

ds_id_to_name = {}
images_list = []
TABLE_IMAGES_LIMIT = 1000

DataJson()["steps"] = OrderedDict(
    {"input_project": 1, "filtering": 2, "images_table": 3, "actions": 4}
)
StateJson()["current_step"] = 1
StateJson()["collapsed_steps"] = {
    "input_project": False,
    "filtering": True,
    "images_table": True,
    "actions": True,
}

images_limit = 0

import asyncio
import concurrent

executor = concurrent.futures.ThreadPoolExecutor()
loop = asyncio.get_event_loop()
