# Request for Help: GTK4 Gtk.FlowBox Layout Issue

## Problem Description
I am building a book shelf application using GTK4 and `libadwaita`. I am using a `Gtk.FlowBox` to display a grid of books, but instead of wrapping horizontally, the books are being displayed in a single vertical column, regardless of the window width or the `set_max_children_per_line` setting.

It seems that each child widget (`BookWidget`) is occupying the full width of the `FlowBox`, forcing the next child to wrap to a new line.

## Current Implementation

### `ShelfGrid` (Inherits from `Gtk.FlowBox`)
```python
class ShelfGrid(Gtk.FlowBox):
    def __init__(self, on_book_selected_callback: Callable[[Book], None]) -> None:
        super().__init__()
        self.on_book_selected = on_book_selected_callback
        self.set_valign(Gtk.Align.START)
        self.set_halign(Gtk.Align.FILL)
        self.set_hexpand(True)
        
        # Configuration from settings
        config = load_config()
        self.set_max_children_per_line(config.get("books_per_line", 10))
        self.set_selection_mode(Gtk.SelectionMode.NONE)
        self.set_column_spacing(12)
        self.set_row_spacing(12)
```

### `BookWidget` (Inherits from `Adw.Bin`)
```python
class BookWidget(Adw.Bin):
    def __init__(self, book: Book, on_click_callback: Callable[[Book], None]) -> None:
        super().__init__()
        self.set_hexpand(False)
        self.set_vexpand(False)
        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.CENTER)
        
        # Layout container
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_hexpand(False)
        box.set_vexpand(False)
        self.set_child(box)

        # Cover image
        image = Gtk.Picture()
        config = load_config()
        width = config.get("cover_width", 120)
        height = config.get("cover_height", 180)
        image.set_size_request(width, height)
        image.set_halign(Gtk.Align.CENTER)
        image.set_valign(Gtk.Align.CENTER)
        image.set_hexpand(False)
        image.set_vexpand(False)
        image.set_content_fit(Gtk.ContentFit.CONTAIN)
        
        # Image loading logic...
        box.append(image)
        
        # Title label
        label = Gtk.Label(label=book.title)
        label.set_halign(Gtk.Align.CENTER)
        box.append(label)
```

### Parent Structure
`MainWindow (Adw.ApplicationWindow)` -> `Gtk.Box (Vertical)` -> `Gtk.ScrolledWindow` -> `ShelfGrid (Gtk.FlowBox)`

## Question
How can I ensure that `Gtk.FlowBox` correctly arranges the `BookWidget` children in a horizontal grid based on the available width and `max_children_per_line`? What properties am I missing or setting incorrectly that causes the children to take up the full width and result in a vertical layout?
