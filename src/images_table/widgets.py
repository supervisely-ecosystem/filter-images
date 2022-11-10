from supervisely.app.widgets import ElementButton, ConfusionMatrix, ClassicTable, GridGallery, NotificationBox

images_table = ClassicTable(fixed_columns_num=0, widget_id="images_table")

images_gallery = GridGallery(columns_number=1, enable_zoom=False, sync_views=True, fill_rectangle=False, widget_id="images_gallery")
