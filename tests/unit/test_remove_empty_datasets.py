"""Copy / Move must never remove a destination dataset that holds images (see DATA_LOSS.md).

The platform's `DatasetInfo.images_count` is a denormalized counter. On the dev instance it once read 0 for a
just-filled dataset (`Tropical/Lemon`, 3 images copied ~7 s earlier) and the app archived that dataset with its
images. `LaggingCountApi` replays that: the counter of the named destination datasets reads 0 although the
images are there (an actual listing shows them). The tests call `apply_action` the way `/apply_action/` does.
"""

from types import SimpleNamespace

import pytest

from fake_api import FakeApi

SOURCE = 3


class LaggingCountApi(FakeApi):
    """`dataset.get_info_by_id(...).images_count` reads 0 for destination datasets named in `lagging`."""

    def __init__(self, lagging=()):
        super().__init__(team_id=1, workspace_id=2, project_id=SOURCE)
        self.lagging = set(lagging)

    def _dataset_info(self, ds_id):
        info = super()._dataset_info(ds_id)
        if info.project_id != SOURCE and info.name in self.lagging:
            info.images_count = 0
        return info


def add_project(api, name, datasets):
    """Existing destination project with the user's own data: datasets = [(name, parent name or None, n_images)]."""
    pid = api._project_create(2, name).id
    by_name = {}
    for ds_name, parent, n_images in datasets:
        ds = api._dataset_create(pid, ds_name, parent_id=by_name[parent].id if parent else None)
        by_name[ds_name] = ds
        for n in range(n_images):
            add_image(api, ds.id, f"own_{ds_name}_{n}.jpg")
    api.calls.clear()
    return pid


def add_image(api, ds_id, name):
    img_id = next(api._ids)
    api.images[img_id] = SimpleNamespace(id=img_id, name=name, dataset_id=ds_id, labels_count=0, tags=[])


@pytest.fixture
def run(app_modules, monkeypatch):
    _, g, _ = app_modules
    import src.actions.functions as functions

    def _run(api, images=None, **action):
        monkeypatch.setattr(g, "api", api)
        monkeypatch.setattr(
            g,
            "project",
            {
                "workspace_id": 2,
                "project_id": SOURCE,
                "name": "Source",
                "dataset_ids": [10, 11],
                "dataset_names": ["root", "child"],
                "project_meta": None,
            },
        )
        src_images = sorted((i for i in api.images.values() if i.dataset_id in (10, 11)), key=lambda i: i.id)
        monkeypatch.setattr(g, "images_list", src_images if images is None else images)
        state = {
            "selected_action": "Copy / Move",
            "move_or_copy": "copy",
            "dstProjectMode": "newProject",
            "dstProjectName": "Filtered",
            "dstDatasetMode": "similarDatasets",
            "dstDatasetName": "ds0",
            "selectedProjectId": None,
            "selectedDatasetName": None,
            "selected_filters": [],
        }
        state.update(action)
        return functions.apply_action(state)

    return _run


def tree(api, project_id):
    """{"root/child": [image names]} of the live (not archived) datasets of a project."""
    datasets = {d.id: d for d in api.datasets.values() if d.project_id == project_id}

    def path(d):
        return f"{path(datasets[d.parent_id])}/{d.name}" if d.parent_id else d.name

    return {path(d): sorted(i.name for i in api.images.values() if i.dataset_id == d.id) for d in datasets.values()}


COPIED = {
    "root": ["0_img_10_0.jpg", "1_img_10_1.jpg"],
    "root/child": ["2_img_11_0.jpg", "3_img_11_1.jpg"],
}


def test_copy_keeps_dataset_whose_images_count_lags(run):
    api = LaggingCountApi(lagging={"child"})  # dev: Tropical/Lemon read images_count=0 after the copy
    project, _ = run(api)
    assert tree(api, project.id) == COPIED
    assert not api.archived_images
    assert not [c for c in api.calls if c[0] == "dataset_remove"]


def test_lagging_count_on_a_whole_branch_does_not_cascade(run):
    # old code: child removed (count 0), then root (count 0, no alive child left) -> the whole tree archived
    api = LaggingCountApi(lagging={"root", "child"})
    project, _ = run(api)
    assert tree(api, project.id) == COPIED
    assert not api.archived_images


def test_move_with_lagging_count_loses_nothing(run):
    # Move removes the source images first; archiving the destination would leave them only in the archive
    api = LaggingCountApi(lagging={"child"})
    project, _ = run(api, move_or_copy="move")
    assert tree(api, project.id) == {
        "root": ["0_img_10_0.jpg", "1_img_10_1.jpg"],
        "root/child": ["2_img_11_0.jpg", "3_img_11_1.jpg"],
    }
    assert tree(api, SOURCE) == {"root": [], "root/child": []}
    assert not api.archived_images


def test_existing_destination_dataset_is_never_removed(run):
    # A top-level dataset that only groups nested datasets has images_count == 0 (direct images only).
    # Old code archived it whenever its count read 0 after the copy -- together with the user's nested data.
    api = LaggingCountApi(lagging={"container"})
    dst = add_project(api, "Existing", [("container", None, 0), ("kept", "container", 2)])
    project, msg = run(
        api,
        dstProjectMode="existingProject",
        selectedProjectId=dst,
        dstDatasetMode="existingDataset",
        selectedDatasetName="container",
    )
    assert project.id == dst
    assert tree(api, dst) == {
        "container": ["0_img_10_0.jpg", "1_img_10_1.jpg", "2_img_11_0.jpg", "3_img_11_1.jpg"],
        "container/kept": ["own_kept_0.jpg", "own_kept_1.jpg"],
    }
    assert not api.archived_images
    assert msg == "Dataset: container"


def test_existing_destination_dataset_kept_even_if_nothing_was_copied(run):
    api = FakeApi()
    dst = add_project(api, "Existing", [("container", None, 0), ("kept", "container", 2)])
    run(
        api,
        images=[],
        dstProjectMode="existingProject",
        selectedProjectId=dst,
        dstDatasetMode="existingDataset",
        selectedDatasetName="container",
    )
    assert tree(api, dst) == {"container": [], "container/kept": ["own_kept_0.jpg", "own_kept_1.jpg"]}
    assert not api.archived_images


def test_new_dataset_that_received_no_images_is_still_removed(run):
    # The intended clean-up stays: a dataset this run created and wrote nothing into is not left behind.
    api = FakeApi()
    project, msg = run(api, images=[], dstDatasetMode="newDataset", dstDatasetName="ds0")
    assert tree(api, project.id) == {}
    assert len([c for c in api.calls if c[0] == "dataset_remove"]) == 1
    assert msg == "Datasets: []"


def test_created_dataset_is_kept_if_a_listing_shows_images(app_modules, monkeypatch):
    # Even a dataset this run wrote nothing into is removed only when an actual listing shows it empty.
    _, g, _ = app_modules
    import src.actions.functions as functions

    api = FakeApi()
    monkeypatch.setattr(g, "api", api)
    pid = api._project_create(2, "Dst").id
    ds = api._dataset_create(pid, "ds0")
    add_image(api, ds.id, "written_by_someone_else.jpg")
    kept = functions.remove_empty_datasets([ds.id], written={}, created_ids={ds.id})
    assert [d.id for d in kept] == [ds.id]
    assert not [c for c in api.calls if c[0] == "dataset_remove"]
