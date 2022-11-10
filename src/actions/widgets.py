from supervisely.app.widgets import SlyTqdm, NotificationBox

action_progress = SlyTqdm(message='', widget_id="action_progress")
warning_before_action = NotificationBox(description="Your source project data WILL BE CHANGED. Apply this action only if you're sure that all settings selected correctly.", box_type='warning', widget_id="warning_before_action")