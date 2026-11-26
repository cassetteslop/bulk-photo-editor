"""Small helpers for rectangles / keep-out maps under rotate and flip."""

import numpy as np

from photo_editor.core.constants import ASPECTS

def rect_transform(r, op):
    x0, y0, x1, y1 = r
    if op == "cw":
        return (1 - y1, x0, 1 - y0, x1)
    if op == "ccw":
        return (y0, 1 - x1, y1, 1 - x0)
    if op == "fh":
        return (1 - x1, y0, 1 - x0, y1)
    if op == "fv":
        return (x0, 1 - y1, x1, 1 - y0)
    return r


def obst_transform(m, op):
    """Same transforms for the square keep-out grid (row = y, column = x)."""
    if m is None:
        return None
    if op == "cw":
        return np.ascontiguousarray(np.rot90(m, -1))
    if op == "ccw":
        return np.ascontiguousarray(np.rot90(m, 1))
    if op == "fh":
        return np.ascontiguousarray(m[:, ::-1])
    if op == "fv":
        return np.ascontiguousarray(m[::-1, :])
    return m


def aspect_ratio(name, size):
    r = ASPECTS.get(name)
    if r == "orig":
        return size[0] / size[1]
    return r
