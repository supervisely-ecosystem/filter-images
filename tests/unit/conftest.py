import pytest
import supervisely as sly
from supervisely.api.api import Api

from fake_api import FakeApi

ENV = {
    "SERVER_ADDRESS": "http://fake.supervisely.local",
    "API_TOKEN": "x" * 128,
    "context.teamId": "1",
    "context.workspaceId": "2",
    "context.userId": "7",
    "modal.state.slyProjectId": "3",
}


@pytest.fixture(scope="session")
def app_modules():
    """Import the app once per session with `sly.Api.from_env` replaced by `FakeApi`.

    The app's modules build widgets and routes at import time, so every test module shares this import;
    a test that needs another fake swaps `g.api` with monkeypatch.
    """
    mp = pytest.MonkeyPatch()
    for key, value in ENV.items():
        mp.setenv(key, value)
    mp.delenv("ENV", raising=False)
    api = FakeApi(team_id=1, workspace_id=2, project_id=3)
    mp.setattr(Api, "from_env", classmethod(lambda cls, *a, **k: api))
    mp.setattr(sly, "FileCache", lambda *a, **k: None)  # would create tempfiles/ inside the repo

    import src.main as main
    import src.sly_globals as g

    yield main, g, api
    mp.undo()
