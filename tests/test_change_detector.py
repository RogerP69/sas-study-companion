from PIL import Image
from change_detector import ChangeDetector


def _solid_image(color: tuple, size=(400, 300)) -> Image.Image:
    img = Image.new("RGB", size, color)
    return img


def test_first_call_never_triggers():
    detector = ChangeDetector(threshold_percent=8.0)
    result = detector.has_changed(_solid_image((255, 0, 0)))
    assert result is False


def test_identical_images_do_not_trigger():
    detector = ChangeDetector(threshold_percent=8.0)
    img = _solid_image((100, 100, 100))
    detector.has_changed(img)
    assert detector.has_changed(img) is False


def test_completely_different_images_trigger():
    detector = ChangeDetector(threshold_percent=8.0)
    detector.has_changed(_solid_image((0, 0, 0)))
    result = detector.has_changed(_solid_image((255, 255, 255)))
    assert result is True


def test_threshold_respected():
    detector_sensitive = ChangeDetector(threshold_percent=1.0)
    detector_tolerant = ChangeDetector(threshold_percent=90.0)

    base = _solid_image((0, 0, 0))
    # Image with roughly 50% pixels changed
    changed = Image.new("RGB", (400, 300))
    pixels = [(255, 255, 255) if i < 150 * 400 else (0, 0, 0) for i in range(400 * 300)]
    changed.putdata(pixels)

    detector_sensitive.has_changed(base)
    detector_tolerant.has_changed(base)

    assert detector_sensitive.has_changed(changed) is True
    assert detector_tolerant.has_changed(changed) is False


def test_reset_clears_previous():
    detector = ChangeDetector(threshold_percent=8.0)
    detector.has_changed(_solid_image((0, 0, 0)))
    detector.reset()
    # After reset, first call should never trigger
    result = detector.has_changed(_solid_image((255, 255, 255)))
    assert result is False
