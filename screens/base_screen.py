class BaseScreen:
    def __init__(self, screen_manager, db_service):
        self.screen_manager = screen_manager
        self.db_service = db_service
        self.app_instance = screen_manager.app
        self.canvas = self.app_instance.canvas
        self.widgets_on_screen = []
        self.canvas_items_on_screen = []
    def clear_screen_elements(self):
        for widget in self.widgets_on_screen: widget.destroy()
        self.widgets_on_screen = []
        for item in self.canvas_items_on_screen: self.canvas.delete(item)
        self.canvas_items_on_screen = []
    def add_widget(self, widget):
        self.widgets_on_screen.append(widget)
        return widget
    def create_canvas_text(self, *args, **kwargs):
        item = self.canvas.create_text(*args, **kwargs)
        self.canvas_items_on_screen.append(item)
        return item
    def create_canvas_image(self, *args, **kwargs):
        item = self.canvas.create_image(*args, **kwargs)
        self.canvas_items_on_screen.append(item)
        return item
    def setup_ui(self): raise NotImplementedError("Subclass harus mengimplementasikan metode setup_ui")