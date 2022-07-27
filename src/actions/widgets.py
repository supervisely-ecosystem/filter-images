from supervisely.app.widgets import SlyTqdm, NotificationBox

action_progress = SlyTqdm(message='')
warning_before_action = NotificationBox("Your source project data MAY BE CHANGED. Apply this action only if you're sure that all settings selected correctly.", box_type='warning')