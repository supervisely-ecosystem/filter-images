"""Contract tests: run the app (uvicorn, as the platform does) on every cases/*.env against a dev instance.

Opt-in: SLY_CONTRACT_TESTS=1 and a dev token in ~/supervisely.env (or SERVER_ADDRESS/API_TOKEN).
Every case first copies its reference project into the sandbox workspace (SLY_CONTRACT_WORKSPACE,
default 733 "agents-sandbox", team SLY_CONTRACT_TEAM, default 1), because every action writes into or
next to its input. Reference projects are only read. Nothing is deleted: the created projects are
printed so they can be cleaned up by hand.

    SLY_CONTRACT_TESTS=1 pytest tests/contract -m contract -s
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest
import requests
from dotenv import dotenv_values, load_dotenv

from .driver import AppDriver

ROOT = Path(__file__).resolve().parents[2]
CASES = sorted((ROOT / "cases").glob("*.env"))

pytestmark = [
    pytest.mark.contract,
    pytest.mark.skipif(os.environ.get("SLY_CONTRACT_TESTS") != "1", reason="set SLY_CONTRACT_TESTS=1 to run"),
]


@pytest.fixture(scope="module")
def api():
    load_dotenv(os.path.expanduser("~/supervisely.env"))
    if not os.environ.get("API_TOKEN"):
        pytest.skip("no dev token")
    import supervisely as sly

    return sly.Api.from_env()


def copy_reference_project(api, src_id: int, workspace_id: int, name: str):
    import supervisely as sly

    dst = api.project.create(workspace_id, name, type=sly.ProjectType.IMAGES, change_name_if_conflict=True)
    api.project.update_meta(dst.id, api.project.get_meta(src_id))
    datasets = api.dataset.get_list(src_id, recursive=True)
    by_id, mapping = {d.id: d for d in datasets}, {}

    def ensure(ds_id):
        if ds_id not in mapping:
            info = by_id[ds_id]
            parent = ensure(info.parent_id) if info.parent_id else None
            mapping[ds_id] = api.dataset.create(dst.id, info.name, parent_id=parent).id
        return mapping[ds_id]

    for ds in datasets:
        images = api.image.get_list(ds.id)
        dst_ds = ensure(ds.id)
        if images:
            api.image.copy_batch_optimized(
                ds.id, images, dst_ds, with_annotations=True, dst_names=[i.name for i in images], skip_validation=True
            )
    return dst


def dataset_counts(api, project_id: int) -> dict[str, int]:
    datasets = api.dataset.get_list(project_id, recursive=True)
    by_id = {d.id: d for d in datasets}

    def path(d):
        return f"{path(by_id[d.parent_id])}/{d.name}" if d.parent_id else d.name

    return {path(d): len(api.image.get_list(d.id)) for d in datasets}


def image_tags(api, project_id: int) -> list[list[dict]]:
    tags = []
    for ds in api.dataset.get_list(project_id, recursive=True):
        tags += [ann["tags"] for ann in (api.annotation.download_json(i.id) for i in api.image.get_list(ds.id))]
    return tags


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def start_app(project_id: int, team_id: int, workspace_id: int, user_id: int, log_path: Path):
    port = free_port()
    env = {
        **os.environ,
        "context.teamId": str(team_id),
        "context.workspaceId": str(workspace_id),
        "context.userId": str(user_id),
        "modal.state.slyProjectId": str(project_id),
        "PYTHONUNBUFFERED": "1",
    }
    env.pop("ENV", None)
    log = open(log_path, "w")  # noqa: SIM115 - closed with the process
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "src.main:g.app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=ROOT,
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
    )
    base = f"http://127.0.0.1:{port}"
    for _ in range(120):
        if proc.poll() is not None:
            raise RuntimeError(log_path.read_text()[-3000:])
        try:
            if requests.get(base + "/", timeout=2).status_code == 200:
                return proc, base
        except requests.RequestException:
            pass
        time.sleep(1)
    proc.kill()
    raise TimeoutError("app did not start")


@pytest.mark.parametrize("case_path", CASES, ids=[c.stem for c in CASES])
def test_case(api, case_path, tmp_path):
    case = dotenv_values(case_path)
    team_id = int(os.environ.get("SLY_CONTRACT_TEAM", "1"))
    workspace_id = int(os.environ.get("SLY_CONTRACT_WORKSPACE", "733"))
    source = copy_reference_project(
        api, int(case["modal.state.slyProjectId"]), workspace_id, f"fi-contract {case_path.stem}"
    )
    print(f"\n[{case_path.stem}] created source copy: project {source.id} in workspace {workspace_id}")

    proc, base = start_app(source.id, team_id, workspace_id, api.user.get_my_info().id, tmp_path / "app.log")
    try:
        app = AppDriver(base)
        app.select_project([n for n in (case.get("DATASETS") or "").split(",") if n])
        state = app.apply_filters(json.loads(case["FILTERS"]), case["PRESET"])
        assert not state["empty_list"]
        assert app.data()["images_list_len"] == int(case["EXPECT_FILTERED"])
        state = app.apply_action(json.loads(case["ACTION"]), source.id)
        data = app.data()
    finally:
        proc.terminate()
        proc.wait(timeout=30)
    assert state["action_finished"], (tmp_path / "app.log").read_text()[-3000:]

    if "EXPECT_DST_DATASETS" in case:
        dst_id = data["dstProjectId"]
        print(f"[{case_path.stem}] created destination: project {dst_id}")
        assert dst_id != source.id
        assert dataset_counts(api, dst_id) == json.loads(case["EXPECT_DST_DATASETS"])
        assert "Project changed by Filter Images app" in api.project.get_info_by_id(dst_id).readme
    else:
        assert "Project changed by Filter Images app" in api.project.get_info_by_id(source.id).readme
    if "EXPECT_SRC_DATASETS" in case:
        counts = dataset_counts(api, source.id)
        for path, count in json.loads(case["EXPECT_SRC_DATASETS"]).items():
            assert counts[path] == count, (path, counts)
    if "EXPECT_IMAGE_TAG" in case:
        expected = json.loads(case["EXPECT_IMAGE_TAG"])
        per_image = [[t for t in tags if t["name"] == expected["name"]] for tags in image_tags(api, source.id)]
        assert (
            sum(1 for tags in per_image if any(t.get("value") == expected["value"] for t in tags)) == expected["count"]
        )
        if expected.get("exclusive"):  # the old value was replaced, not added next to it
            assert all(len(tags) <= 1 for tags in per_image)
    if "EXPECT_NO_OBJECT_TAG" in case:
        for ds in api.dataset.get_list(source.id, recursive=True):
            for image in api.image.get_list(ds.id):
                ann = api.annotation.download_json(image.id)
                assert not [t for o in ann["objects"] for t in o["tags"] if t["name"] == case["EXPECT_NO_OBJECT_TAG"]]
    if "EXPECT_NO_IMAGE_TAGS" in case:
        assert all(tags == [] for tags in image_tags(api, source.id))
