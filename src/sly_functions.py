import supervisely as sly

import src.sly_globals as g


def shutdown_app():
    try:
        sly.app.fastapi.shutdown()
    except KeyboardInterrupt:
        sly.logger.info("Application shutdown successfully")


def get_project_meta(refresh: bool = False) -> sly.ProjectMeta:
    """Project meta of the selected project.

    `g.project["project_meta"]` is read when the project is selected; classes and tags created after that are
    missing from it. Pass `refresh=True` to read the current meta from the server (and update the cache).
    """
    if refresh or g.project["project_meta"] is None:
        meta_json = g.api.project.get_meta(g.project["project_id"])
        g.project["project_meta"] = sly.ProjectMeta.from_json(meta_json)
    return g.project["project_meta"]


def annotation_from_json(ann_json: dict) -> sly.Annotation:
    """Parse an annotation of the selected project.

    Tries the cached meta first. If it does not fit (a class or tag referenced by the annotation was created or
    changed after the project was selected), reads the current meta from the server once and retries.
    """
    try:
        return sly.Annotation.from_json(ann_json, get_project_meta())
    except Exception:  # unknown class/tag, or a changed shape/value type: retry with the current meta
        return sly.Annotation.from_json(ann_json, get_project_meta(refresh=True))
