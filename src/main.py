from fastapi import Request, Depends

import src.sly_globals as g

import src.input_project


@g.app.get("/")
def read_index(request: Request):
    return g.templates_env.TemplateResponse('index.html', {'request': request})

