## v0.8.3 (2026-05-05)

### Fix

- serialize database updates and optimize progress reporting
- ignore missing cover files and update tests
- ignore missing files during cache clear
- make clear library reactive
- grid reactivity and test stability
- restore grid layout reactivity and update test
- grid reactivity and test stability
- make settings changes reactive

## v0.8.2 (2026-05-04)

## v0.8.1 (2026-05-04)

### Perf

- parallelize library scanning with ThreadPoolExecutor

## v0.8.0 (2026-05-04)

### Feat

- **ui**: implement multi-book drag-and-drop

## v0.7.1 (2026-05-04)

### Refactor

- address SOLID/DRY violations and implement sorting strategy pattern

## v0.7.0 (2026-05-04)

### Feat

- **ui**: add appearance mode selection (light/dark/system) to settings

## v0.6.0 (2026-05-04)

### Feat

- **ui**: add empty state page and search keyboard shortcut

## v0.5.0 (2026-05-04)

### Feat

- support keyword-based (order-independent) book search
- support multiple library directories
- **ui**: modernize dialogs and add multi-selection with drag-and-drop
- add recursive option to folder import
- **ui**: debounce config saves in MainWindow
- add show/hide titles option
- add progress reporting to folder imports
- add category creation to import dialog
- consolidate import workflow and add category selection
- implement clear library feature and fix dialog transient parent
- implement double-click to open and add context menu open action
- implement thumbnail resizing for book covers
- migrate ShelfGrid to Gtk.GridView and resolve book opening issues
- **repository**: implement pagination and lazy loading for book retrieval
- use MetadataExtractor for imports and add metadata editing
- persist UI state for categories, sidebar and sort
- implement metadata extraction, search, sorting and library config
- **ui**: implement category deletion in sidebar
- implement bookshelves categories and sidebar navigation

### Fix

- apply books_per_line setting to grid column count
- pre-select current category in context menu dropdown
- sidebar category sync and bulk categorization during folder import
- correctly handle async response in Adw.AlertDialog.choose
- restore import buttons and improve clear library reliability
- improve cleanup logic and refine clear library UI flow
- ensure settings popups are correctly parented to avoid being hidden
- ensure sidebar is refreshed when clearing library
- **ui**: prevent unresponsive and overlapping error dialogs
- **database**: close all thread-local connections in BookRepository.close
- use user_data_dir for database path in main.py
- **ui**: ensure thread safety and visibility checks in GTK callbacks
- resolve TypeError in Gtk.FileDialog.select_folder and fix test regression
- resolve title visibility reset on save
- resolve toggle auto-reset
- resolve shelf_grid attribute error
- title visibility toggle
- resolve signal handler return value
- retrieve widget from wrapper box
- robust metadata extraction in scanner
- add missing progress bar methods
- make cover extraction robust
- use Gtk.Dialog for better import interaction
- resolve FileDialog callback assertion
- resolve import dialog structure
- resolve file dialog assertion
- explicitly select import type
- address pre-commit hook issues
- resolve technical debt issues
- implement SQLite WAL mode and config validation
- replace deprecated GTK methods with modern equivalents
- **ui**: correct Adw.Toast initialization and title setting
- **ui**: replace dialog.destroy with dialog.close in main window
- address technical debt items from AGENTS.md
- **scanner**: improve portability of directory check in cleanup_missing
- **extractor**: use correct OPF metadata for EPUB cover extraction
- improve error handling in book extraction services
- **ui**: execute import and cleanup operations in background threads
- normalize created_at to datetime in BookRepository
- resolve bugs and design issues from code review
- **ui**: fix book widget click handlers and implement double click
- update sidebar toggle icons and layout

### Refactor

- use dropdown for category selection in book context menu
- **controller**: move business logic from MainController to BookService
- address code review findings and improve stability

### Perf

- **extractor**: optimize cover hash generation using file metadata
- **ui**: load initial book list asynchronously
- move book search from Python to SQL
- reuse database connections per thread in BookRepository

## v0.4.0 (2026-04-28)

### Feat

- implement zoom level and grid layout configuration, expand UI tests

## v0.3.0 (2026-04-28)

### Feat

- add burger menu with file and folder import functionality
- implement main window and controller
- implement basic UI components for book shelf
- implement book scanner service
- implement book repository for metadata persistence

## v0.2.0 (2026-04-28)

### Feat

- implement cover extraction service
