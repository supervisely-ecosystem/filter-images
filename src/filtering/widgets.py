from supervisely.app.widgets import ElementButton, ConfusionMatrix, ClassicTable, GridGallery, NotificationBox

images_table = ClassicTable(fixed_columns_num=0)

images_gallery = GridGallery(columns_number=3, enable_zoom=False, sync_views=True)
