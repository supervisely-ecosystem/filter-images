"""Drive a running filter-images server over HTTP the way the browser does (full state in every POST)."""

from __future__ import annotations

import copy
import time

import requests


class AppDriver:
    def __init__(self, base_url: str, timeout: float = 600):
        self.base = base_url.rstrip("/")
        self.timeout = timeout

    def post(self, path: str, state: dict | None = None) -> requests.Response:
        body = {} if state is None else {"state": state, "context": {}}
        response = requests.post(self.base + path, json=body, timeout=self.timeout)
        response.raise_for_status()
        return response

    def state(self) -> dict:
        return self.post("/sly/state").json()

    def data(self) -> dict:
        return self.post("/sly/data").json()

    def wait_until(self, predicate, first_sleep: float = 1.5) -> dict:
        time.sleep(first_sleep)  # the long handlers return before they flip their "busy" flag
        deadline = time.time() + self.timeout
        while time.time() < deadline:
            state = self.state()
            if predicate(state):
                return state
            time.sleep(1)
        raise TimeoutError("app did not finish in time")

    @staticmethod
    def resolve(value, data: dict):
        """Replace "tag:<name>" / "class:<name>" placeholders with the ids the page shows."""
        if isinstance(value, str) and value.startswith("tag:"):
            return next(t["id"] for t in data["available_tags"] if t["name"] == value[4:])
        if isinstance(value, str) and value.startswith("class:"):
            return next(c["id"] for c in data["available_classes"] if c["name"] == value[6:])
        if isinstance(value, dict):
            return {k: AppDriver.resolve(v, data) for k, v in value.items()}
        if isinstance(value, list):
            return [AppDriver.resolve(v, data) for v in value]
        return value

    def select_project(self, dataset_names: list[str]) -> None:
        state, data = self.state(), self.data()
        if dataset_names:
            tree_key = next(k for k in state if k.startswith("TreeSelectAutoId"))
            checkbox_key = next(k for k in state if k.startswith("CheckboxAutoId"))
            flat = []

            def walk(items):
                for item in items:
                    flat.append(item)
                    walk(item.get("children") or [])

            walk(data[tree_key]["items"])
            state[checkbox_key]["checked"] = False
            state[tree_key]["value"] = [
                {"id": i["id"], "label": i["label"]} for i in flat if i["label"] in dataset_names
            ]
        self.post("/download_project_button/button_clicked_cb", state)

    def apply_filters(self, filters: list[dict], preset: str) -> dict:
        state = self.state()
        state["selected_filters"] = self.resolve(copy.deepcopy(filters), self.data())
        state["current_preset"] = preset
        self.post("/apply_filters/", state)
        return self.wait_until(lambda s: not s["filtering"])

    def apply_action(self, action: dict, source_project_id: int) -> dict:
        data = self.data()
        action = self.resolve(copy.deepcopy(action), data)
        if action.get("selectedProjectId") == "source":
            action["selectedProjectId"] = source_project_id
        state = self.state()
        state.update({k: v for k, v in action.items() if k != "selectedDatasetName"})
        self.post("/select_action/", state)
        state = self.state()
        if action.get("dstProjectMode") == "existingProject":
            self.post("/select_dst_project/", state)
            state = self.state()
            state["selectedDatasetName"] = action["selectedDatasetName"]
        if action["selected_action"] == "Assign tag" and action.get("assign_tag_is_existing") == "true":
            self.post("/select_tag_to_assign/", state)
            state = self.state()
            state["tag_to_assign_value"] = action["tag_to_assign_value"]
        if action["selected_action"].startswith("Remove specific"):
            self.post("/select_tag_to_remove/", state)
            state = self.state()
        self.post("/apply_action/", state)
        return self.wait_until(lambda s: not s["action_process"], first_sleep=3)
