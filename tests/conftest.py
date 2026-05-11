"""Pytest configuration and fixtures for eshelf."""

import gi  # noqa: E402
import pytest  # noqa: E402

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def init_gtk():
    """Initialize GTK for tests."""
    app = Gtk.Application(application_id="org.eshelf.test")
    # Just registering the application is often enough to initialize
    # the necessary GTK internals for widget instantiation in tests.
    app.register()
    yield app
