import numpy as np


class Location:
    def __init__(
        self, x, y, x_lim=(0, 100), y_lim=(0, 100), flipped=False, precision=2
    ):
        self._original_x = x
        self._original_y = y
        self.x_lim = x_lim
        self.y_lim = y_lim
        self.flipped = flipped
        self.precision = precision
        self.x = self.transform(self._original_x, self.x_lim, flipped)
        self.y = self.transform(self._original_y, self.y_lim, flipped)

    def transform(self, value, lim, flipped):
        if not self.is_valid:
            return value

        if flipped:
            return round(lim[1] - value, self.precision)
        return round(value, self.precision)

    def distance(self, other):
        return np.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)

    def to_dict(self):
        return {"x": self.x, "y": self.y}

    @property
    def is_valid(self):
        return not np.isnan(self._original_x) and not np.isnan(self._original_y)

    def __repr__(self) -> str:
        return f"{self.x}, {self.y}"

    def __getitem__(self, key):
        if key == 0:
            return self.x
        elif key == 1:
            return self.y
        raise KeyError(f"Invalid key: {key}")

    def __sub__(self, other):
        return Location(self.x - other.x, self.y - other.y)


def get_end_location(event, flipped):
    if len(event["positions"]) != 2:
        return Location(np.nan, np.nan, flipped=flipped)

    return Location(
        event["positions"][1]["x"],
        event["positions"][1]["y"],
        flipped=flipped,
    )


def get_start_location(event, flipped):
    if len(event["positions"]) != 2:
        return Location(np.nan, np.nan, flipped=flipped)
    return Location(
        event["positions"][0]["x"],
        event["positions"][0]["y"],
        flipped=flipped,
    )
