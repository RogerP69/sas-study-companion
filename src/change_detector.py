from PIL import Image, ImageChops

_THUMBNAIL_SIZE = (200, 150)
_CHANGE_SENSITIVITY = 30  # sum of RGB channel diffs to count a pixel as "changed"


class ChangeDetector:
    def __init__(self, threshold_percent: float = 8.0):
        self._threshold = threshold_percent / 100.0
        self._previous: Image.Image | None = None

    def has_changed(self, current: Image.Image) -> bool:
        thumb = current.resize(_THUMBNAIL_SIZE).convert("RGB")
        if self._previous is None:
            self._previous = thumb
            return False
        diff = ImageChops.difference(self._previous, thumb)
        pixels = list(diff.getdata())
        changed = sum(1 for r, g, b in pixels if r + g + b > _CHANGE_SENSITIVITY)
        self._previous = thumb
        return (changed / len(pixels)) >= self._threshold

    def reset(self) -> None:
        self._previous = None
