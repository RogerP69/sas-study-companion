from unittest.mock import MagicMock, patch
from PIL import Image


def test_capture_returns_pil_image():
    mock_screenshot = MagicMock()
    mock_screenshot.size = (1920, 1080)
    mock_screenshot.bgra = b"\x00" * (1920 * 1080 * 4)

    mock_sct = MagicMock()
    mock_sct.__enter__ = lambda s: s
    mock_sct.__exit__ = MagicMock(return_value=False)
    mock_sct.monitors = [None, {"left": 0, "top": 0, "width": 1920, "height": 1080}]
    mock_sct.grab.return_value = mock_screenshot

    with patch("screen_capture.mss.mss", return_value=mock_sct):
        from screen_capture import capture
        result = capture(monitor_index=1)

    assert isinstance(result, Image.Image)
    assert result.size == (1920, 1080)


def test_capture_uses_correct_monitor_index():
    mock_screenshot = MagicMock()
    mock_screenshot.size = (2560, 1440)
    mock_screenshot.bgra = b"\x00" * (2560 * 1440 * 4)

    mock_sct = MagicMock()
    mock_sct.__enter__ = lambda s: s
    mock_sct.__exit__ = MagicMock(return_value=False)
    mock_sct.monitors = [
        None,
        {"left": 0, "top": 0, "width": 1920, "height": 1080},
        {"left": 1920, "top": 0, "width": 2560, "height": 1440},
    ]
    mock_sct.grab.return_value = mock_screenshot

    with patch("screen_capture.mss.mss", return_value=mock_sct):
        from screen_capture import capture
        capture(monitor_index=2)
        mock_sct.grab.assert_called_once_with(
            {"left": 1920, "top": 0, "width": 2560, "height": 1440}
        )
