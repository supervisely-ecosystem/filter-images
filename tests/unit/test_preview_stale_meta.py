"""The preview and the tag actions must not rely on the project meta cached at project selection.

`g.project["project_meta"]` is read once, when the project is selected. If a class or tag is created afterwards
and the first filtered image uses it, `sly.Annotation.from_json` with the cached meta raises. Before the fix the
error escaped `show_preview`, so "Apply filters" never cleared `filtering` and the gallery stayed in `loading`
(the preview hung forever), and a click on a table row left `loading_preview` set, which blocks every later click.
"""

import concurrent.futures
import copy

import pytest
import supervisely as sly
from fastapi.testclient import TestClient

from fake_api import PROJECT_META

LOADED = sly.ProjectMeta.from_json(PROJECT_META)  # what the app read when the project was selected
# Created on the server after that: a class and a tag the first image now uses.
CURRENT = LOADED.add_obj_class(sly.ObjClass("kiwi", sly.Polygon, sly_id=102)).add_tag_meta(
    sly.TagMeta("reviewed", sly.TagValueType.NONE, sly_id=204)
)


def ann_with_new_class_and_tag():
    return {
        "size": {"height": 10, "width": 10},
        "tags": [{"name": "fruit", "value": None}, {"name": "reviewed", "value": None}],
        "objects": [
            {
                "classTitle": "kiwi",
                "geometryType": "polygon",
                "points": {"exterior": [[1, 1], [5, 1], [5, 5]], "interior": []},
                "tags": [{"name": "reviewed", "value": None}],
            }
        ],
    }


class InlineExecutor:
    """Runs the long handlers synchronously; the done-callback sees the outcome like with the real pool."""

    def submit(self, fn, *args):
        future = concurrent.futures.Future()
        try:
            future.set_result(fn(*args))
        except Exception as e:  # noqa: BLE001 - the route's done-callback logs it
            future.set_exception(e)
        return future


class MetaServer:
    """Server-side meta, changed by someone else after the app loaded the project."""

    def __init__(self, meta):
        self.meta = meta
        self.reads = 0

    def get_meta(self, project_id):
        self.reads += 1
        return self.meta.to_json()


@pytest.fixture
def env(app_modules, monkeypatch):
    _, g, api = app_modules
    monkeypatch.setattr(g, "executor", InlineExecutor())
    server = MetaServer(LOADED)
    monkeypatch.setattr(api.project, "get_meta", server.get_meta)
    return g, api, server


def state():
    from supervisely.app import StateJson

    return copy.deepcopy(dict(StateJson()))


def data():
    from supervisely.app import DataJson

    return copy.deepcopy(dict(DataJson()))


def post(client, path, st=None):
    response = client.post(path, json={"state": state() if st is None else st, "context": {}})
    assert response.status_code == 200, response.text
    return response


def select_project(client):
    post(client, "/new_action/")
    post(client, "/download_project_button/button_clicked_cb")
    assert state()["current_step"] == 2


def gallery_annotation(d):
    gallery = d["images_gallery"]
    assert gallery["loading"] is False
    assert len(gallery["content"]["annotations"]) == 1
    return next(iter(gallery["content"]["annotations"].values()))


def test_preview_of_first_filtered_image_with_class_created_after_selection(env, monkeypatch):
    g, api, server = env
    client = TestClient(g.app)
    select_project(client)
    assert g.project["project_meta"].get_obj_class("kiwi") is None  # cached at selection

    server.meta = CURRENT  # a class and a tag are added in the labeling tool, and the first image uses them
    monkeypatch.setattr(api.annotation, "download_json", lambda img_id: ann_with_new_class_and_tag())
    st = state()
    st["selected_filters"] = []
    post(client, "/apply_filters/", st)

    st, d = state(), data()
    assert st["filtering"] is False, "Apply filters never finished"
    assert st["current_step"] == 4
    assert st["preview_error"] == ""
    figures = gallery_annotation(d)["figures"]
    assert [f["classTitle"] for f in figures] == ["kiwi"]
    assert "reviewed" in gallery_annotation(d)["title"]
    assert g.project["project_meta"].get_obj_class("kiwi") is not None  # the cache was refreshed


def test_preview_reads_the_meta_only_when_the_cached_one_does_not_fit(env, monkeypatch):
    g, api, server = env
    import src.images_table.functions as table_functions

    monkeypatch.setitem(g.project, "project_meta", LOADED)
    server.meta = CURRENT
    image_id = next(iter(api.images))

    table_functions.show_preview(image_id)  # FakeApi's default annotation fits the cached meta
    assert server.reads == 0

    monkeypatch.setattr(api.annotation, "download_json", lambda img_id: ann_with_new_class_and_tag())
    table_functions.show_preview(image_id)
    assert server.reads == 1
    table_functions.show_preview(image_id)  # now cached
    assert server.reads == 1


def test_failed_preview_clears_loading_and_is_shown(env, monkeypatch):
    g, api, server = env
    import src.images_table.functions as table_functions

    client = TestClient(g.app)
    select_project(client)
    post(client, "/apply_filters/", {**state(), "selected_filters": []})
    errors = []
    monkeypatch.setattr(table_functions.sly.logger, "warning", lambda msg, *a, **k: errors.append(msg))
    # The class is not in the server's meta either (e.g. deleted meanwhile): the preview cannot be built.
    monkeypatch.setattr(api.annotation, "download_json", lambda img_id: ann_with_new_class_and_tag())

    image_id = next(iter(api.images))
    st = state()
    st["images_table"]["selected_row"] = {
        "selectedRow": 0,
        "selectedColumn": 5,
        "selectedRowData": dict.fromkeys(["id", "dataset name", "item name", "image", "objects number", "show"])
        | {"id": image_id},
    }
    post(client, "/images_table/cell_clicked_cb", st)

    st, d = state(), data()
    assert st["loading_preview"] is False, "a failed preview blocks every later click"
    assert d["images_gallery"]["loading"] is False
    assert "kiwi" in st["preview_error"]
    assert errors and str(image_id) in errors[0]

    # The next click on a good image works and clears the message.
    empty_ann = {"size": {"height": 4, "width": 4}, "tags": [], "objects": []}
    monkeypatch.setattr(api.annotation, "download_json", lambda img_id: empty_ann)
    post(client, "/images_table/cell_clicked_cb", st)
    assert state()["preview_error"] == ""
    assert data()["images_gallery"]["loading"] is False


class ObjectTagApi:
    """Records which figure tags the action removes."""

    def __init__(self):
        self.removed = []

    def download_json_batch(self, ds_id, image_ids):
        anns = []
        for n, img_id in enumerate(image_ids):
            ann = ann_with_new_class_and_tag()
            ann["objects"][0]["id"] = img_id * 10
            ann["objects"][0]["tags"] = [{"id": img_id * 100 + n, "tagId": 202, "name": "score", "value": 1}]
            anns.append(ann)
        return anns

    def remove_tag_from_object(self, tag_meta_id, figure_id, tag_id):
        self.removed.append((tag_meta_id, figure_id, tag_id))


def test_remove_tag_from_objects_works_on_classes_created_after_selection(env, monkeypatch):
    g, api, server = env
    from src.actions import functions

    server.meta = CURRENT
    monkeypatch.setitem(g.project, "project_meta", LOADED)
    images = [i for i in api.images.values() if i.dataset_id == 10]
    monkeypatch.setattr(g, "images_list", images)
    objects = ObjectTagApi()
    monkeypatch.setattr(api.annotation, "download_json_batch", objects.download_json_batch, raising=False)
    monkeypatch.setattr(api.advanced, "remove_tag_from_object", objects.remove_tag_from_object, raising=False)

    functions.remove_specific_tag_from_objects({"tag_to_remove": 202})

    assert sorted(fig for _, fig, _ in objects.removed) == sorted(i.id * 10 for i in images)


def test_remove_all_image_tags_includes_tags_created_after_selection(env, monkeypatch):
    g, api, server = env
    from src.actions import functions

    server.meta = CURRENT.add_tag_meta(sly.TagMeta("late", sly.TagValueType.NONE, sly_id=203))
    monkeypatch.setitem(g.project, "project_meta", LOADED)
    images = [i for i in api.images.values() if i.dataset_id == 10]
    monkeypatch.setattr(g, "images_list", images)
    api.calls.clear()

    functions.remove_tags_from_images()

    removed = [c for c in api.calls if c[0] == "remove_tags"]
    assert removed and 203 in removed[0][1]
