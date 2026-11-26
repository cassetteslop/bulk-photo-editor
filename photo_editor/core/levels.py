"""Per-channel Levels (black point, gamma, white point) -> lookup tables."""

class Levels:
    """Black point / gamma / white point for the master (RGB) and R, G, B channels."""
    CHANNELS = ("RGB", "R", "G", "B")

    def __init__(self, d=None):
        self.d = {c: [0, 1.0, 255] for c in self.CHANNELS}
        if d:
            for c in self.CHANNELS:
                self.d[c] = list(d[c])

    def copy(self):
        return Levels(self.d)

    def reset(self, channel=None):
        for c in ([channel] if channel else self.CHANNELS):
            self.d[c] = [0, 1.0, 255]

    @staticmethod
    def _f(x, black, gamma, white):
        t = (x - black) / max(white - black, 1)
        t = min(max(t, 0.0), 1.0)
        return 255.0 * (t ** (1.0 / gamma))

    def luts(self):
        """768-entry table (R, G, B) for Image.point()."""
        mb, mg, mw = self.d["RGB"]
        table = []
        for c in "RGB":
            cb, cg, cw = self.d[c]
            for x in range(256):
                v = self._f(self._f(x, cb, cg, cw), mb, mg, mw)
                table.append(int(round(min(255.0, max(0.0, v)))))
        return table

    def is_identity(self):
        return self.luts() == list(range(256)) * 3
