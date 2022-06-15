from fastapi import Request, Depends

import src.sly_globals as g

import src.example_card


@g.app.get("/")
def read_index(request: Request):
    return g.templates_env.TemplateResponse('index.html', {'request': request})

