# Modernization notes: filter-images (hardened-image move)

Mechanical move of `filter-images` from the shared legacy image to the hardened base, same SDK.
App structure is unchanged on purpose (`sly_globals.py`, Jinja templates, route modules).
Base: `origin/master` @ 2d37aea. Branch `local/modernize`, nothing committed.

## Behaviour contract (kept)

GUI session started from an images project (`context_menu: images_project`, `workspace_tasks`), served by
`uvicorn src.main:g.app`. Four steps:

1. **Input**: team / workspace / project / dataset tree (`SelectDatasetTree`, nested datasets, "select all").
2. **Filters**: presets (All images, With one object or more, Without any objects, Without objects of class,
   Labeled by me, Has issues) or custom filters (filename, with/without image tag + value, objects with/without
   tag, objects of class / without class with count range, by annotator, tagged by annotator, issues), combined with AND.
3. **Table** of filtered images (first 1000) with a preview.
4. **Action** on all filtered images: Copy / Move (new project in the source workspace or an existing project;
   new dataset, an existing dataset, or the source structure with nesting kept; names prefixed `<idx>_`),
   Delete, Assign tag (new tag with type/value, or an existing tag whose old value is replaced),
   Remove all image tags, Remove a specific tag from images or from objects.
   The destination (or source) project readme gets an "Applied filters" block; workflow lineage: source project in,
   result project out. "Select next action" restarts at step 1, "Finish app" stops the session.

## Changes

1. **Startup crash on Python 3.14 fixed.** `sly_globals.py` called `asyncio.get_event_loop()` at import; on 3.14
   this raises when there is no running loop, and uvicorn 0.52 imports the app before starting its loop
   (reproduced: the old code exits with `RuntimeError: There is no current event loop` in the hardened image).
   The two long handlers (`/apply_filters/`, `/apply_action/`) now call `g.executor.submit(...)` and attach the same
   done-callback; they still return immediately and log failures. No other code change was needed.
2. **Image** `supervisely/data-operations:6.74.34` (Python 3.8) → `supervisely/base-py-sdk-hardened:6.74.34`
   (Python 3.14.7). Entry point unchanged.
3. `pyproject.toml`: ruff (`py314`) and pytest config added. Legacy lint patterns in `src/` (star-import route
   registration, same-named route handlers, FastAPI `Depends` defaults, import order with side effects, long lines)
   are listed in `per-file-ignores` instead of being rewritten; tests are linted fully.
4. Added `tests/unit` (offline), `tests/contract` (opt-in, dev instance), `cases/*.env`.

## Image decision

Bare hardened image: `dev_requirements.txt` holds only `supervisely==6.74.34` and the app imports nothing else.
What `data-operations` adds on top of `base-py-sdk` (libzbar0, pyzbar, moviepy, imageio-ffmpeg, imutils, decord) is
unused here. The hardened image has fastapi 0.136, uvicorn 0.52, websockets 13.1 (uvicorn's `ws=auto` picks it),
jinja2 and httpx. Tag checked on Docker Hub.
**SDK stays 6.74.34**: `instance_version` 6.17.22 allows [6.74.29, 6.74.35) (`supervisely/versions.json`); a newer SDK
needs a higher `instance_version` (product decision). CI: `release.yml` only calls `common.yml`; there is no
`build-image` job, so nothing unused gets built.

## Verification (2026-10-25, dev.internal.supervisely.com, instance 6.18.7)

- **Unit/smoke** `pytest tests/unit`: 6 passed (13 with the data-loss tests, see below) on macOS Python 3.14.3 and inside `base-py-sdk-hardened:6.74.34`
  (Python 3.14.7, amd64). The app is imported with a fake `Api` and driven over HTTP with `TestClient`: index page,
  select project → filters → copy with nested structure, assign existing tag (old value removed first),
  failing action / failing filter unlock the UI and are logged. On the old code the same suite fails at import
  (`RuntimeError: There is no current event loop`).
- **ruff** `ruff check .` and `ruff format --check tests`: clean.
- **Old vs new on dev**: old code (`origin/HEAD`, `data-operations:6.74.34`, Python 3.8) and new code (hardened,
  Python 3.14) each ran in development mode on its own sandbox copy of the reference project, driven over HTTP like
  the browser; source copy and destination project (datasets tree, image names/hashes, annotations, image and object
  tags, meta, readme) compared after the run. 8 cases on #1317 (nested), #46, #27, #9390: copy with structure,
  move of a subset to a new dataset, assign new number tag, replace string tag, remove object tag, delete, remove
  all image tags, copy into the existing source dataset. All identical; the only difference is the random color the
  SDK gives a newly created tag.
- **Contract tests** `SLY_CONTRACT_TESTS=1 pytest tests/contract -m contract`: 8 passed (one per `cases/*.env`).
- **Production run in the real image**: `ENV=production` on debug task 62730, `base-py-sdk-hardened:6.74.34`, entry
  point from `config.json`: copy of #1317 with the source structure → project #9570 (9 datasets, 22 images), relative
  "open in annotation tool" links, workflow calls without warnings or errors, "Finish app" shut the server down (exit 0).

## Found and fixed (pre-existing, also in the published app)

- **Data loss in Copy / Move clean-up** (`remove_empty_datasets`, since v1.3.3): destination datasets were archived
  when the server's denormalized `images_count` read 0, which happened on dev about 7 s after a copy (`Tropical/Lemon`,
  project 9424). With Move, or with an existing destination dataset (the user's nested data), the loss is worse.
  The clean-up now removes only datasets this run created, wrote nothing into, and an actual listing shows empty.
  See `DATA_LOSS.md` (root cause, reproduction, production risk, ecosystem sweep) and
  `tests/unit/test_remove_empty_datasets.py`.

- **Preview hangs on a class/tag created after the project was selected** (also in the published app). `show_preview`
  parsed the annotation with `g.project["project_meta"]`, read once at project selection; a label of a newer class
  (or a newer tag) raised, the error escaped, and "Apply filters" never cleared `filtering` (gallery stuck loading,
  step 3 never opened); a table click left `loading_preview` set, which blocks every later click.
  Now the annotation is parsed with the cached meta and, if that fails, once more with the meta re-read from the
  server (`sly_functions.annotation_from_json`; no extra request when the cache fits). Preview errors are logged and
  shown above the preview, and both loading flags are cleared in `finally`. The tag-removal actions read the current
  meta: "Remove all tags" missed tags created after selection, and "Remove specific tag (from objects)" failed on
  newer classes. Copy / Move does not use the cached meta (the SDK merges the current metas); Assign tag already
  reads the current meta. Not changed: the filter dropdowns still list the classes/tags of the selection time
  (re-select the project to see new ones). Tests: `tests/unit/test_preview_stale_meta.py`.

## Found, not fixed (pre-existing, outside a mechanical move)

- Destination dataset message lists datasets in set-iteration order (varies between runs); cosmetic.
- `pyproject.toml` `[project]`/`[tool.uv.sources]` (local SDK path) and `uv.lock`, `local.env` with ids from another
  instance, `create_venv.sh`: left as they were.

## Not verified

- The page in a real browser on the platform (all GUI checks were HTTP-driven); the TreeSelect value the browser
  sends when a parent dataset is ticked (tests select leaf datasets).
- "Labeled by me", annotator and issue filters, "Remove specific tag (from images)" against dev (unit-level only for
  the dispatch path they share).
