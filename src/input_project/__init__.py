from pathlib import Path

from jinja2 import Environment

from supervisely.app import StateJson, DataJson

import src.sly_globals as g

from src.input_project.routes import *
from src.input_project.functions import *
from src.input_project.widgets import *