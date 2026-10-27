"""Assign tag with a new tag must not overwrite project meta with the copy loaded at project selection.

Before the fix `assign_tag` added the tag to `g.project["project_meta"]` (read when the project was selected)
and wrote that back with `update_meta`, deleting classes and tag metas created in the meantime together with
their labels project-wide (DATA_LOSS.md, second finding).
"""

import pytest
import supervisely as sly


class MetaStore:
    """Server-side project meta that someone else changes after the app loaded it."""

    def __init__(self, meta):
        self.meta = meta
        self.writes = []

    def get_meta(self, project_id):
        return self.meta.to_json()

    def update_meta(self, project_id, meta_json):
        self.meta = sly.ProjectMeta.from_json(meta_json)
        self.writes.append(self.meta)


def new_tag_state(name):
    return {
        "tag_to_assign_value": None,
        "assign_tag_is_existing": "false",
        "tag_to_assign": None,
        "tag_to_assign_name": name,
        "tag_to_assign_value_type": str(sly.TagValueType.NONE),
        "tag_to_assign_values": [],
        "tag_to_assign_applicable_to": sly.TagApplicableTo.ALL,
    }


@pytest.fixture
def store(app_modules, monkeypatch):
    _, g, api = app_modules
    loaded = sly.ProjectMeta(obj_classes=[sly.ObjClass("lemon", sly.Rectangle)])
    added_later = loaded.add_obj_class(sly.ObjClass("kiwi", sly.Polygon)).add_tag_meta(
        sly.TagMeta("reviewed", sly.TagValueType.NONE)
    )
    store = MetaStore(added_later)
    monkeypatch.setitem(g.project, "project_meta", loaded)
    monkeypatch.setattr(api.project, "get_meta", store.get_meta)
    monkeypatch.setattr(api.project, "update_meta", store.update_meta)
    return store


def test_new_tag_keeps_classes_and_tags_added_after_selection(app_modules, store):
    from src.actions import functions

    try:
        functions.assign_tag(new_tag_state("checked"))
    except Exception:  # noqa: BLE001 - the rest of assign_tag needs more of the fake API; only the meta write matters
        pass

    assert store.writes, "the new tag meta was not written"
    written = store.writes[0]
    assert written.get_obj_class("kiwi") is not None
    assert written.get_tag_meta("reviewed") is not None
    assert written.get_tag_meta("checked") is not None


def test_new_tag_with_existing_name_is_rejected(app_modules, store):
    from src.actions import functions

    with pytest.raises(ValueError, match="already exists"):
        functions.assign_tag(new_tag_state("reviewed"))
    assert store.writes == []
