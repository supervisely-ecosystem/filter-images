from fastapi import Depends, HTTPException
from numpy import False_

import supervisely

import src.actions.widgets as card_widgets
import src.actions.functions as card_functions

from supervisely.app import DataJson, StateJson
from supervisely.app.fastapi import run_sync
from supervisely.app.widgets import ElementButton

import src.sly_functions as f

import src.sly_globals as g


@g.app.post('/apply_action/')
def apply_action_clicked(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    state["action_process"] = True
    run_sync(state.synchronize_changes())
    card_functions.apply_action(state)
    state["action_process"] = False_
    run_sync(state.synchronize_changes())
    run_sync(DataJson().synchronize_changes())

    f.shutdown_app()