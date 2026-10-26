# Data loss in Copy / Move: datasets removed by a stale `images_count`

Status: root cause confirmed on dev, fixed in this worktree (`src/actions/functions.py`), not committed.
The published app (v1.3.3 to v1.4.6, `origin/HEAD` 2d37aea) has the bug. The hardened-image move did not introduce it.
`src/actions/functions.py` at `origin/HEAD` is byte-identical to the pre-fix worktree file.

## 1. What happened (dev, 2026-10-25)

The reviewer ran "copy with structure" from #1317 (nested) into new project **9424** "fi-cmp nested new".
`Tropical/Lemon` was missing afterwards. Evidence, all read-only:

| Time (UTC) | Event | Source |
|---|---|---|
| 04:11:47–51 | 9 destination datasets created; Lemon = **48194** | `datasets.info` of 48185–48195 |
| 04:12:01.342 | an image (id 7598709) from another agent's job lands in dataset 48184 of project 9423 | `images.info` |
| ~04:12:01.4 | Lemon's 3 images are inserted (ids 7598710–12); progress 19/22 at 04:12:01.590 | app log, image ids |
| 04:12:03.47 | Orange's 3 images are inserted; progress 22/22 | Orange `updatedAt`, app log |
| **04:12:09.760** | `disable_dataset` 48194, by the token user. This is the only dataset removal in the team in that window | `team.get_activity` |
| 04:12:09.765 | readme written; it lists 8 destination datasets, without Lemon | project 9424 readme |

Images 7598710–12 still exist, but archived (`images.info` returns "archived"). So the app's own
`remove_empty_datasets` archived Lemon: it read `images_count == 0` for Lemon about 7 s after its images were committed.
In the same pass, datasets copied before and after Lemon (Pineapple, Orange) read correctly.

## 2. Root cause

`remove_empty_datasets` (old code, `src/actions/functions.py:61-81`, called from `copy_images:100` and `move_images:134`)
archives every destination dataset whose `DatasetInfo.images_count == 0` and that has no surviving child
**in its own list**. It uses no other evidence.

- `images_count` comes from `datasets.info` and is a denormalized counter of **direct** images only.
  For #1317, `Tropical` and `Temperate` read 0 while their children hold 22 images. The counter is eventually
  correct: a scan of 800 datasets in ws 733 found 0 persistent mismatches against a listing. It is not
  guaranteed fresh right after a write, though, and on 2026-10-25 it was stale for at least ~7 s under concurrent
  load from other agents. The SDK adds no caching (`DatasetApi.get_info_by_id` posts `datasets.info` each call), so
  the stale value came from the server.
- The deletion is irreversible from the app's side and does not check the app's own knowledge. The app knows
  exactly how many images it just wrote into each dataset, and by construction every created leaf dataset received
  images. It also never lists the dataset's actual contents.

Every way the old code can delete a non-empty dataset or more than it should:

1. **Stale count on a created dataset (observed).** A leaf that just received images is archived with them.
   Modes: "copy/move with source structure" (`similarDatasets`) and "new dataset" (`newDataset`).
2. **Cascade up the tree.** Once all children are removed, a parent that holds only nested datasets (direct count 0)
   has no "alive child" and is archived too. If every child of `Tropical` reads stale, the whole branch goes.
   Reproduced on dev: 6 datasets and 16 images archived.
3. **Move loses the data from both sides.** `move_batch_optimized` removes the source images before the clean-up runs.
   A wrongly archived destination dataset then leaves the moved images only in the archive.
4. **"Existing dataset" destination: the user's pre-existing data.** The selected existing dataset is passed to the
   same clean-up. It is often a top-level dataset that only groups nested datasets, so its direct `images_count` is 0.
   If that count is stale after the copy (or if 0 images were copied), the app archives the user's dataset.
   The server then archives **all nested datasets and their images** with it. Those children are not in the app's
   list, so the "alive child" guard never sees them. Reproduced on dev: copying 6 images into the source copy's own
   `Tropical` archived `Tropical` plus Banana, Mango, Pineapple, Lemon and Orange (16 pre-existing images).
5. Not the cause, checked and ruled out: SDK caching (none), retries (`images.bulk.add` retries only on NONUNIQUE
   and raises otherwise), `dataset.create(change_name_if_conflict=True)` (always a new dataset, never an existing
   one), executor change in the new code (old and new run the identical `functions.py`; the 1/6 vs 0/5 split is chance).

## 3. Reproduction

**Offline, deterministic** (`tests/unit/test_remove_empty_datasets.py`, fake API in `tests/fake_api.py`).
`LaggingCountApi` returns `images_count = 0` for named destination datasets while their images are listed.
The fake's `dataset.remove` cascades to nested datasets and images, like the server.

| Test | Old code | Fixed |
|---|---|---|
| `test_copy_keeps_dataset_whose_images_count_lags` (the Lemon case) | fails: child archived | passes |
| `test_lagging_count_on_a_whole_branch_does_not_cascade` | fails: whole tree archived | passes |
| `test_move_with_lagging_count_loses_nothing` | fails: moved images only in archive | passes |
| `test_existing_destination_dataset_is_never_removed` | fails: user's container + nested data archived | passes |
| `test_existing_destination_dataset_kept_even_if_nothing_was_copied` | fails | passes |
| `test_new_dataset_that_received_no_images_is_still_removed` (intended clean-up kept) | passes | passes |
| `test_created_dataset_is_kept_if_a_listing_shows_images` | n/a (new signature) | passes |

`pytest tests/unit`: 13 passed on macOS Python 3.14 and inside `supervisely/base-py-sdk-hardened:6.74.34`.
Before the fix: 6 failed, 7 passed. `ruff check .` and `ruff format --check tests` are clean.

**Dev, natural trigger: not reproducible on demand.** It appeared once in 11 reviewer runs (1/6 new code, 0/5 old).
My attempts to trigger it: 30 sequential copy+read cycles (150 reads, including immediate reads),
10 full replays of the app's call sequence on #1317 (dry-run clean-up, 90 dataset decisions), and 45 trials of
4–8 concurrent copies with reads at 0/0.3/1/3 s (240 dataset reads). Result: **0 stale reads**. The lag needs
server load that I could not recreate. Rate seen so far: about 1 in 11 runs during the busy multi-agent window,
0 in ~500 reads afterwards.

**Dev, deterministic with fault injection** (`dev_run.py` in the session scratchpad, not in the repo).
The script imports the app's action code (old export of `origin/HEAD` or the worktree) and calls `apply_action`
against the real dev API on fresh sandbox copies of #1317. `dataset.get_info_by_id().images_count` reads 0 for the
named datasets, which is what dev returned for Lemon. Every run had a 100% outcome:

| Scenario (injected stale count) | Old code | Fixed |
|---|---|---|
| copy with structure, `Lemon` | Lemon archived (9634), the reviewer's exact outcome | 9 datasets, 22 images (9636) |
| copy with structure, whole `Tropical` branch | 6 datasets archived (9638) | all kept (9640) |
| move with structure, `Lemon` | source emptied, Lemon archived (9652) | all 22 in destination (9654) |
| copy into existing `Tropical` (container) | Tropical + 5 nested archived, 16 pre-existing images (9655) | kept, 6 copied in (9656) |
| no injection: structure / new dataset / existing dataset | n/a | unchanged results (9661 / 9659 / 9657) |

## 4. Fix (worktree, `src/actions/functions.py`)

`remove_empty_datasets(ds_ids, written, created_ids)` removes a dataset only when **all** of these hold:

- this run created it (`newDataset` / `similarDatasets`). An existing destination dataset is never removed;
- this run wrote 0 images into it (`written`, counted per destination in `copy_images` / `move_images`);
- no other dataset of this run is still nested in it;
- an actual listing (`image.get_list(ds, limit=1)` and `dataset.get_list(project, parent_id=ds)`) shows no images
  and no child datasets.

`images_count` is no longer read for the decision. In normal runs nothing is removed, as before: every created leaf
receives images and every created parent has children. The one intended clean-up stays: a "new dataset" that
received nothing is still removed. Cost: no extra calls for datasets that received images. Created parents cost 2
list calls each, instead of the old second `get_info_by_id` pass. User-visible behaviour, readme and result message
are unchanged.

Test support changes: `tests/unit/conftest.py` now imports the app once per session (shared by both test modules),
and `tests/fake_api.py` gained `dataset.get_list(parent_id=...)` and a cascading, archiving `dataset.remove`.

## 5. Production risk

- **Since:** v1.3.3 (107adeb, 2023-09-29, "Preserve project structure"), which added the `images_count == 0 → remove`
  loop for all destination datasets, including an existing one. v1.4.5 (1476314, 2026-06-27, nested datasets) made it
  the bottom-up `remove_empty_datasets` and made case 4 much worse. Nested containers have a direct count of 0, and
  archiving one takes its subtree. Current release v1.4.6 has it. The app has ~2.3k runs in total.
- **User actions that trigger it:** Copy or Move to any destination ("new dataset", "keep source structure",
  "existing dataset"). The deciding read happens right after the writes, so it is most likely on a busy instance.
  Delete and the tag actions are not affected.
- **What is lost and how bad:**
  - Copy: destination dataset(s) archived. The source is intact, so copying again recovers.
  - Move: the moved images exist only in the archived destination dataset(s), so the user sees them as gone.
  - Existing-dataset destination: the user's own dataset, all its nested datasets and their pre-existing images
    are archived. This is the worst case.
  - Recoverability: `datasets.remove` archives, it does not hard-delete. The data stays in the DB until an admin
    `remove_permanently` or instance clean-up. The activity log records `disable_dataset`, and a `restore_dataset`
    action exists platform-side, but SDK 6.74.34 has no dataset restore. Users need support or an admin to get it
    back, and the app's readme and message silently omit the removed dataset, so users may not notice.
- **Detection in production:** `team.get_activity(..., filter_actions=["disable_dataset"])` entries a few seconds after
  a filter-images task wrote into the same project.

## 6. Same pattern in the ecosystem (read-only sweep)

Searched 146 local clones (`git grep origin/HEAD`) and 533 mirrors (`git grep HEAD`). First pass: files that both
read `images_count` / `items_count` and call a dataset/project/image remove or archive. Second pass: all
`remove_empty*` / `*empty_datasets*` helpers.

| Location | Deletes on a count? | Verdict |
|---|---|---|
| `filter-images/src/actions/functions.py:77` (origin/HEAD) | `images_count == 0` → `dataset.remove` | **The bug** (fixed here) |
| `sys-add-project-from-ecosystem/src/functions.py:208-216` (`remove_empty_partial_projects`, called from `add_project.py:108` after HTTP 402) | `if project.items_count: keep else project.remove` | **Same pattern, lower risk.** A project this task created during a failed upload is archived if its counter reads 0/None. A stale count loses the partially uploaded items (ecosystem sample data, re-addable). The fix is to list items instead (`image.get_list(..., limit=1)` per dataset). |
| `mirror:sys-archiver/src/main.py:830`, `mirror:archive-old-projects-on-community-edition/src/main.py:657` | `images_count == 0/None` → project marked `archivation_status="obsolete"`, skipped | Not data loss. A stale 0 permanently excludes a non-empty project from archiving (wrong flag, safe direction). |
| `data-commander/src/main.py:3397-3426` (`ensure_datasets_deletion`, 2943) | removes destination datasets with `len(created_items) == 0` | No. It decides from what it wrote (the pattern this fix adopts). |
| `data-commander/src/main.py:1618` `_count_items_in_tree`, `:2195` move removes source datasets | counts only for progress; removal after a successful copy | No. |
| `mirror:transfer-labeled-items/src/main.py:179,230` | `accepted_images_count != 0` selects jobs; removes by job entity ids | No (not count-based deletion). |
| `RT-DETR`, `mmsegmentation`, `yolov8`, `train-mmdetection-v3`, `mirror:unet`, SDK `nn/training/train_app.py:3012` | remove benchmark temp projects they created; counts are metrics | No. |
| `mirror:instance-performance-meter/src/utils.py:412`, `mirror:solutions-data-organization/src/sly_functions.py:216` | remove image ids they track | No. |
| SDK `convert/video/sly/sly_video_converter.py:465` | `items_count == 0` decides whether to create a new multi-view project | Not deletion. A stale 0 would upload into the wrong-interface project. |

## 7. Dev artifacts

All in ws 733, name prefix `dlfi-rc`, created by this investigation; nothing was deleted except by the app inside
these copies. 42 projects: 9593, 9596-9609 (probe/replays), 9617-9629 (concurrency probes), 9633-9661 (dev runs).
Reviewer's failing run, read only: source 9420, destination 9424, archived dataset 48194.

## Second data-loss path: Assign tag overwrote project meta (found by the independent reviewer, fixed)

- **What:** "Assign tag" with a *new* tag added the tag to the project meta loaded when the project was
  selected (`g.project["project_meta"]`) and wrote that copy back with `update_meta`
  (`src/actions/functions.py`, origin/HEAD lines 185-187, unchanged since 342a247, 2022-07-20). Classes and
  tag metas created in the project after the app loaded it were deleted — with every label and tag of those
  classes, project-wide.
- **Fix:** read the current meta right before the write, add only the new tag meta, and refuse a "new" tag
  whose name already exists ("choose it as an existing tag"), instead of the old `DuplicateKeyError`.
- **Tests:** `tests/unit/test_assign_tag_meta.py` (2 tests) — both fail on the old code, pass on the fix.
  A millisecond-wide read-modify-write window remains between `get_meta` and `update_meta` (the SDK has no
  atomic meta merge).
- **Not verified on dev** (offline tests only).
