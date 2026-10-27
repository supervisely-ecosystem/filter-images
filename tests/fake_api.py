"""In-memory stand-in for the few `sly.Api` calls the app makes (offline tests only).

Filters are not evaluated: `image.get_filtered_list` / `image.get_list(filters=...)` return every image of
the dataset and record the query, which is enough to drive the app's flow end to end.
"""

from __future__ import annotations

import itertools
from types import SimpleNamespace


class Info(SimpleNamespace):
    """Info object that can be a dict key (`dataset.get_tree` returns {DatasetInfo: children})."""

    __hash__ = object.__hash__


PROJECT_META = {
    "classes": [{"id": 101, "title": "lemon", "shape": "rectangle", "color": "#FF0000"}],
    "tags": [
        {"id": 201, "name": "fruit", "value_type": "none", "color": "#00FF00", "applicable_type": "all"},
        {"id": 202, "name": "score", "value_type": "any_number", "color": "#0000FF", "applicable_type": "all"},
    ],
}


def _ann(height: int = 10, width: int = 10) -> dict:
    return {
        "size": {"height": height, "width": width},
        "tags": [{"tagId": 201, "name": "fruit", "value": None}],
        "objects": [
            {
                "classTitle": "lemon",
                "geometryType": "rectangle",
                "points": {"exterior": [[1, 1], [5, 5]], "interior": []},
                "tags": [],
            }
        ],
    }


class FakeApi:
    """Two-level project (`root` -> `child`) with two images per dataset."""

    def __init__(self, team_id: int = 1, workspace_id: int = 2, project_id: int = 3):
        self.server_address = "http://fake.supervisely.local"
        self.calls: list[tuple] = []
        self._ids = itertools.count(1000)
        self.team_id, self.workspace_id, self.project_id = team_id, workspace_id, project_id
        self.projects = {
            project_id: SimpleNamespace(
                id=project_id,
                name="Source",
                type="images",
                workspace_id=workspace_id,
                team_id=team_id,
                reference_image_url=None,
                readme="",
                items_count=4,
            )
        }
        self.datasets = {
            10: Info(id=10, name="root", parent_id=None, project_id=project_id),
            11: Info(id=11, name="child", parent_id=10, project_id=project_id),
        }
        self.images = {}
        self.archived_images = {}
        for ds_id in (10, 11):
            for n in range(2):
                img_id = ds_id * 100 + n
                self.images[img_id] = SimpleNamespace(
                    id=img_id,
                    name=f"img_{ds_id}_{n}.jpg",
                    dataset_id=ds_id,
                    labels_count=1,
                    tags=[{"tagId": 201, "value": None}],
                    path_original=f"/h5/img_{img_id}.jpg",
                )

        self.team = SimpleNamespace(get_list=lambda: [SimpleNamespace(id=team_id, name="team")])
        self.workspace = SimpleNamespace(get_list=lambda team: [SimpleNamespace(id=workspace_id, name="ws")])
        self.user = SimpleNamespace(get_team_members=lambda team: [SimpleNamespace(id=7, login="annotator")])
        self.app = SimpleNamespace(
            workflow=SimpleNamespace(
                add_input_project=lambda pid: self.calls.append(("workflow_input", pid)),
                add_output_project=lambda pid: self.calls.append(("workflow_output", pid)),
            )
        )
        self.project = SimpleNamespace(
            get_info_by_id=lambda pid: self.projects[pid],
            get_list=lambda ws: [p for p in self.projects.values() if p.workspace_id == ws],
            get_meta=lambda pid: PROJECT_META,
            create=self._project_create,
            edit_info=self._project_edit_info,
            update_meta=lambda pid, meta: self.calls.append(("update_meta", pid)),
        )
        self.dataset = SimpleNamespace(
            get_list=self._dataset_list,
            get_tree=self._dataset_tree,
            get_info_by_id=self._dataset_info,
            create=self._dataset_create,
            remove=self._dataset_remove,
            get_info_by_name=lambda pid, name: next(
                d for d in self.datasets.values() if d.project_id == pid and d.name == name
            ),
        )
        self.image = SimpleNamespace(
            get_filtered_list=self._get_filtered_list,
            get_list=self._get_list,
            get_info_by_id=lambda img_id, force_metadata_for_links=True: self.images[img_id],
            preview_url=lambda url, w, h: f"{url}?{w}x{h}",
            copy_batch_optimized=self._copy_batch,
            move_batch_optimized=self._move_batch,
            remove_batch=self._remove_batch,
            add_tag_batch=lambda ids, tag_id, value, progress_cb=None: self.calls.append(
                ("add_tag", sorted(ids), tag_id, value)
            ),
        )
        self.annotation = SimpleNamespace(download_json=lambda img_id: _ann())
        self.advanced = SimpleNamespace(
            remove_tags_from_images=lambda tag_ids, image_ids, progress_cb=None: self.calls.append(
                ("remove_tags", sorted(tag_ids), sorted(image_ids))
            )
        )

    # ---- projects
    def _project_create(self, workspace_id, name, type=None, change_name_if_conflict=False):
        pid = next(self._ids)
        self.projects[pid] = SimpleNamespace(
            id=pid,
            name=name,
            type="images",
            workspace_id=workspace_id,
            team_id=self.team_id,
            reference_image_url=None,
            readme="",
            items_count=0,
        )
        self.calls.append(("project_create", workspace_id, name))
        return self.projects[pid]

    def _project_edit_info(self, pid, readme=None):
        self.projects[pid].readme = readme
        self.calls.append(("edit_readme", pid))

    # ---- datasets
    def _dataset_list(self, project_id, recursive=False, parent_id=None):
        if parent_id is not None:  # like the SDK: direct children of parent_id
            return [d for d in self.datasets.values() if d.project_id == project_id and d.parent_id == parent_id]
        return [d for d in self.datasets.values() if d.project_id == project_id and (recursive or d.parent_id is None)]

    def _dataset_tree(self, project_id):
        def children(parent):
            return {
                d: children(d.id)
                for d in self.datasets.values()
                if d.project_id == project_id and d.parent_id == parent
            }

        return children(None)

    def _dataset_info(self, ds_id):
        d = self.datasets[ds_id]
        count = sum(1 for i in self.images.values() if i.dataset_id == ds_id)
        return SimpleNamespace(**vars(d), images_count=count)

    def _dataset_create(self, project_id, name, parent_id=None, change_name_if_conflict=False):
        ds_id = next(self._ids)
        self.datasets[ds_id] = Info(id=ds_id, name=name, parent_id=parent_id, project_id=project_id)
        self.calls.append(("dataset_create", project_id, name, parent_id))
        return self._dataset_info(ds_id)

    def _dataset_remove(self, ds_id):
        """Archive like the server: the dataset, its nested datasets and all their images disappear."""
        self.calls.append(("dataset_remove", ds_id))
        for child in [d.id for d in self.datasets.values() if d.parent_id == ds_id]:
            self._dataset_remove(child)
        for img_id in [i.id for i in self.images.values() if i.dataset_id == ds_id]:
            self.archived_images[img_id] = self.images.pop(img_id)
        del self.datasets[ds_id]

    # ---- images
    def _get_filtered_list(
        self, ds_id, filters, force_metadata_for_links=True, limit=None, return_first_response=False
    ):
        self.calls.append(("filtered_list", ds_id, filters))
        items = [i for i in self.images.values() if i.dataset_id == ds_id][:limit]
        return items, {"total": len(items)}

    def _get_list(self, ds_id, filters=None, force_metadata_for_links=True, limit=None, return_first_response=False):
        self.calls.append(("list", ds_id, filters))
        items = [i for i in self.images.values() if i.dataset_id == ds_id][:limit]
        return (items, {"total": len(items)}) if return_first_response else items

    def _copy_batch(self, src_ds, infos, dst_ds, with_annotations=True, progress_cb=None, dst_names=None, **kw):
        for info, name in zip(infos, dst_names, strict=True):
            new_id = next(self._ids)
            self.images[new_id] = SimpleNamespace(**{**vars(info), "id": new_id, "name": name, "dataset_id": dst_ds})
        if progress_cb:
            progress_cb(len(infos))

    def _move_batch(self, src_ds, infos, dst_ds, with_annotations=True, progress_cb=None, dst_names=None, **kw):
        for info, name in zip(infos, dst_names, strict=True):
            self.images[info.id].dataset_id, self.images[info.id].name = dst_ds, name
        if progress_cb:
            progress_cb(len(infos))

    def _remove_batch(self, ids, progress_cb=None, batch_size=None):
        for img_id in ids:
            del self.images[img_id]
        if progress_cb:
            progress_cb(len(ids))
