"""Offline smoke test of the whole GUI flow on the image's Python (3.14).

The app is imported once (its modules build widgets and routes at import time) with `sly.Api.from_env`
replaced by `FakeApi`, then driven over HTTP with `TestClient` the way the browser does it: every POST
carries the full page state. Long handlers (apply filters / apply action) run on `g.executor`; the
tests wait for them through a recording executor.
"""

import concurrent.futures
import copy
import time

import pytest
from fastapi.testclient import TestClient


class RecordingExecutor:
    def __init__(self):
        self._pool = concurrent.futures.ThreadPoolExecutor()
        self.futures = []

    def submit(self, fn, *args):
        future = self._pool.submit(fn, *args)
        self.futures.append(future)
        return future

    def drain(self):
        concurrent.futures.wait(self.futures)
        time.sleep(0.05)  # done-callbacks run right after the waiters are released


@pytest.fixture(scope="module")
def env(app_modules):
    main, g, api = app_modules
    mp = pytest.MonkeyPatch()
    mp.setattr(g, "executor", RecordingExecutor())
    yield main, g, api
    mp.undo()


@pytest.fixture
def client(env):
    main, g, _ = env
    return TestClient(g.app)


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


def select_project_and_filter(client, g, filters=None):
    post(client, "/new_action/")  # "SELECT NEXT ACTION": back to step 1, as after a finished action
    post(client, "/download_project_button/button_clicked_cb")
    st = state()
    assert st["current_step"] == 2
    st["selected_filters"] = filters or []
    post(client, "/apply_filters/", st)
    g.executor.drain()


def test_import_needs_no_event_loop(env):
    _, g, _ = env
    # asyncio.get_event_loop() at import raised on Python 3.14 (uvicorn imports the app before its loop runs)
    assert not hasattr(g, "loop")


def test_index_page_renders(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "sly-stepper" in response.text


def test_copy_into_new_project_keeps_nested_structure(env, client):
    _, g, api = env
    select_project_and_filter(client, g)
    st, d = state(), data()
    assert st["current_step"] == 4 and not st["filtering"] and not st["empty_list"]
    assert d["images_list_len"] == 4
    assert {row[2] for row in d["images_table"]["table_data"]["data"]} == {
        "img_10_0.jpg",
        "img_10_1.jpg",
        "img_11_0.jpg",
        "img_11_1.jpg",
    }
    assert st["apply_text"] == "APPLY TO 4 IMAGES"

    st.update(
        selected_action="Copy / Move",
        move_or_copy="copy",
        dstProjectMode="newProject",
        dstProjectName="Filtered",
        dstDatasetMode="similarDatasets",
    )
    post(client, "/apply_action/", st)
    g.executor.drain()

    st, d = state(), data()
    assert st["action_finished"] and not st["action_process"]
    new_pid = d["dstProjectId"]
    assert api.projects[new_pid].name == "Filtered"
    new_ds = {ds.id: ds for ds in api.datasets.values() if ds.project_id == new_pid}
    by_name = {ds.name: ds for ds in new_ds.values()}
    assert set(by_name) == {"root", "child"}
    assert by_name["child"].parent_id == by_name["root"].id
    copied = sorted((new_ds[i.dataset_id].name, i.name) for i in api.images.values() if i.dataset_id in new_ds)
    assert copied == [
        ("child", "2_img_11_0.jpg"),
        ("child", "3_img_11_1.jpg"),
        ("root", "0_img_10_0.jpg"),
        ("root", "1_img_10_1.jpg"),
    ]
    assert ("workflow_input", 3) in api.calls and ("workflow_output", new_pid) in api.calls
    assert "Project changed by Filter Images app" in api.projects[new_pid].readme
    assert d["dstDatasetMsg"] == "Datasets: ['root', 'child']"


def test_assign_existing_tag_replaces_old_value(env, client):
    _, g, api = env
    select_project_and_filter(client, g)
    st = state()
    st.update(selected_action="Assign tag", assign_tag_is_existing="true", tag_to_assign=201, tag_to_assign_value=None)
    post(client, "/apply_action/", st)
    g.executor.drain()
    image_ids = sorted(i.id for i in api.images.values() if api.datasets[i.dataset_id].project_id == 3)
    assert ("remove_tags", [201], image_ids[:2]) in api.calls
    assert ("add_tag", image_ids[:2], 201, None) in api.calls
    assert state()["action_finished"]


def test_failed_action_unlocks_ui_and_is_logged(env, client, monkeypatch):
    _, g, _ = env
    import src.actions.routes as action_routes

    warnings = []
    monkeypatch.setattr(action_routes, "logger", type("L", (), {"warn": staticmethod(warnings.append)}))
    select_project_and_filter(client, g)
    st = state()
    st.update(
        selected_action="Copy / Move",
        move_or_copy="copy",
        dstProjectMode="newProject",
        dstDatasetMode="newDataset",
        dstDatasetName="",
        action_finished=False,
    )
    post(client, "/apply_action/", st)
    g.executor.drain()
    assert state()["action_process"] is False and state()["action_finished"] is False
    assert warnings and "Dataset name can" in warnings[0]


def test_failed_filtering_resets_flag_and_is_logged(env, client, monkeypatch):
    _, g, _ = env
    import src.filtering.routes as filtering_routes

    warnings = []
    monkeypatch.setattr(filtering_routes, "logger", type("L", (), {"warn": staticmethod(warnings.append)}))
    select_project_and_filter(
        client, g, filters=[{"name": "By Filename", "type": "images_filename", "data": {"value": None}}]
    )
    assert state()["filtering"] is False
    assert warnings and "Filename can" in warnings[0]
