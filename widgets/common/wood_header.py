"""Dezente Holzmaserung als skalierbare Grafik, ohne Bildabhaengigkeit."""
from math import sin
from kivy.graphics import Color, Line, Rectangle


class WoodHeader:
    def __init__(self, widget):
        self.widget = widget
        self.bands = []
        self.grain = []
        with widget.canvas.before:
            for index in range(24):
                tone = 0.009 * sin(index * 1.7)
                Color(0.91 + tone, 0.83 + tone, 0.70 + tone, 1)
                self.bands.append(Rectangle())
            for index in range(46):
                Color(0.48, 0.32, 0.16, 0.07 if index % 3 else 0.12)
                self.grain.append(Line(width=0.6))
        widget.bind(pos=self.update, size=self.update)
        self.update()

    def update(self, *_):
        w = self.widget
        for index, band in enumerate(self.bands):
            band.pos = (w.x, w.y + w.height * index / len(self.bands))
            band.size = (w.width, w.height / len(self.bands) + 1)
        for index, line in enumerate(self.grain):
            y = w.y + w.height * (index + 0.5) / len(self.grain)
            line.points = [coordinate for step in range(21)
                           for coordinate in (w.x + w.width * step / 20,
                                              y + sin(step * 0.7 + index) * min(1.2, w.height / 100))]
