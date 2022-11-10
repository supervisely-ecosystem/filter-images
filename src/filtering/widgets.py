from supervisely.app.widgets import ElementButton, ConfusionMatrix, ClassicTable, GridGallery, NotificationBox

reselect_filters_button = ElementButton(text='<i style="margin-right: 5px" class="zmdi zmdi-rotate-left"></i>reselect',
                                         button_type='warning', button_size='small', plain=True, widget_id="reselect_filters_button")

no_images_box = NotificationBox(description="No images for your request. Please choose other filters.", box_type='warning', widget_id="no_images_box")