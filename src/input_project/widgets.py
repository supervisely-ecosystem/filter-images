from supervisely.app.widgets import SelectDatasetTree, ElementButton, SlyTqdm, DoneLabel

import src.sly_globals as g
from supervisely.app.widgets.notification_box.notification_box import NotificationBox

# Tree selector: shows full dataset hierarchy and allows selecting any nested dataset.
# SelectDatasetTree builds many internal sub-widgets, so the app runs with
# auto_widget_id=True (see sly_globals.create); all app-level widgets keep explicit ids.
project_selector = SelectDatasetTree(
    project_id=g.PROJECT_ID,
    multiselect=True,
    select_all_datasets=True,
    team_is_selectable=True,
    workspace_is_selectable=True,
    show_select_all_datasets_checkbox=True,
    widget_id="project_selector",
)

download_project_button = ElementButton(
    text="SELECT", button_type="primary", widget_id="download_project_button"
)
# TODO: add icon supporting for ElementButton
reselect_project_button = ElementButton(
    text='<i style="margin-right: 5px" class="zmdi zmdi-rotate-left"></i>reselect',
    button_type="warning",
    button_size="small",
    plain=True,
    widget_id="reselect_project_button",
)

project_downloaded_done_label = DoneLabel(
    text="Project and datasets selected", widget_id="project_downloaded_done_label"
)
ds_not_selected = NotificationBox(
    description="Datasets not selected.", box_type="error", widget_id="ds_not_selected"
)
