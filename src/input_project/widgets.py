from supervisely.app.widgets import ProjectSelector, ElementButton, SlyTqdm, DoneLabel

import src.sly_globals as g

project_selector = ProjectSelector(team_id=g.TEAM_ID, workspace_id=g.WORKSPACE_ID,
                                   project_id=g.PROJECT_ID, team_is_selectable=True,
                                   datasets_is_selectable=True)

download_project_button = ElementButton(text='SELECT', button_type='primary')
# TODO: add icon supporting for ElementButton
reselect_project_button = ElementButton(text='<i style="margin-right: 5px" class="zmdi zmdi-rotate-left"></i>reselect',
                                         button_type='warning', button_size='small', plain=True)

project_downloaded_done_label = DoneLabel(text="Project and datasets selected")