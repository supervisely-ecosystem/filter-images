from supervisely.app.widgets import ElementButton, ConfusionMatrix, ClassicTable, GridGallery, NotificationBox

images_table = ClassicTable(fixed_columns_num=6)

images_gallery = GridGallery(columns_number=3, enable_zoom=False, sync_views=True)

add_filter_button = ElementButton(text="+", button_type="success", button_size="medium")
apply_filters_button = ElementButton(text="APPLY FILTER", button_type="primary", button_size="medium")
remove_all_filters_button = ElementButton(text="CLEAR", button_type="danger", button_size="medium")
