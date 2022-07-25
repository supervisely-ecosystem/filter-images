from fastapi import Request, Depends

import src.sly_globals as g

import src.input_project
import src.filtering
import src.images_table
import src.actions


@g.app.get("/")
def read_index(request: Request):
    return g.templates_env.TemplateResponse('index.html', {'request': request})

