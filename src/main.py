from fastapi import Request, Depends

import src.sly_globals as g

import src.input_project
import src.filtering
import src.images_table
import src.actions

from supervisely.app import StateJson
from supervisely.app.fastapi.subapp import _MainServer

# v2 widgets (e.g. SelectDatasetTree) register their value_changed routes on the
# shared _MainServer singleton instead of g.app. This legacy app is served as g.app, so
# include those routes here, after all widgets are constructed.
g.app.include_router(_MainServer().get_server().router)


# v2 widget routes read the current StateJson on the server (without a state
# dependency), relying on a middleware that syncs client state on every request — present
# on the /sly subapp but not on g.app. Mirror it so handlers see the up-to-date state.
@g.app.middleware("http")
async def _sync_state_from_request(request, call_next):
    await StateJson.from_request(request)
    return await call_next(request)


@g.app.get("/")
def read_index(request: Request):
    return g.templates_env.TemplateResponse("index.html", {"request": request})
