from pathlib import Path

from jinja2 import Environment

from supervisely.app import StateJson, DataJson

import src.sly_globals as g

from src.example_card.card_handlers import *
from src.example_card.card_functions import *
from src.example_card.card_widgets import *


##############
# init fields
##############

StateJson()['exampleField'] = "My Example Value in STATE"
DataJson()['exampleField'] = "My Example Value in DATA"


##############
# init routes
##############

g.app.add_api_route('/some_post_request_from_frontend/', card_handlers.example_route, methods=["POST"])


