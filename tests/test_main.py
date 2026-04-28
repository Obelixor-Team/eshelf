"""Tests for the main entry point."""

from unittest.mock import MagicMock, patch

from src.main import main


@patch("src.main.MainController")
@patch("src.main.Adw.Application")
@patch("os.makedirs")
def test_main_execution(
    mock_makedirs: MagicMock,
    mock_adw_app: MagicMock,
    mock_controller: MagicMock,
) -> None:
    """Test that main() initializes the controller and application."""
    mock_app_instance = mock_adw_app.return_value

    main()

    # Verify controller initialization
    mock_controller.assert_called_once()

    # Verify application initialization
    mock_adw_app.assert_called_once()

    # Verify application run was called
    mock_app_instance.run.assert_called_once()
