from supervisely.app.widgets import ElementButton, ConfusionMatrix, ClassicTable, GridGallery, NotificationBox

images_table = ClassicTable(fixed_columns_num=6)

images_gallery = GridGallery(columns_number=3, enable_zoom=False, sync_views=True)

add_filter_button = ElementButton(text="+", button_type="", button_size="")
remove_filter_button = ElementButton(text="x", button_type="", button_size="")
apply_filters_button = ElementButton(text="APPLY FILTER", button_type="", button_size="")
remove_all_filters_button = ElementButton(text="CLEAR", button_type="", button_size="")
