import os
from pathlib import Path

from fastapi import FastAPI
from supervisely.sly_logger import logger
from starlette.staticfiles import StaticFiles

import supervisely
from supervisely.app.fastapi import create, Jinja2Templates

app_root_directory = str(Path(__file__).parent.absolute().parents[0])
logger.info(f"App root directory: {app_root_directory}")

# api = supervisely.Api.from_env()
app = FastAPI()
sly_app = create()

app.mount("/sly", sly_app)
app.mount("/static", StaticFiles(directory=os.path.join(app_root_directory, 'static')), name="static")

templates_env = Jinja2Templates(directory=os.path.join(app_root_directory, 'templates'))

