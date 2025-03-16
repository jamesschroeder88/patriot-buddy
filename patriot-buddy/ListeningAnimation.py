from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (QWidget)


class ListeningAnimation(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(140, 140)

        # Color scheme
        self.wave_color = QColor(26, 127, 64)  # Green
        self.center_color = QColor(255, 214, 0)  # Yellow

        self.circle_radius = 50
        self.animation_progress = 0.0

        # Animation timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)

        # Wave properties
        self.wave_count = 3
        self.waves = []
        for i in range(self.wave_count):
            self.waves.append(0.0)  # Initial scale values

        self.is_animating = False

    def start_animation(self):
        self.is_animating = True
        self.timer.start(50)  # Update every 50ms

    def stop_animation(self):
        self.is_animating = False
        self.timer.stop()
        # Reset waves
        for i in range(self.wave_count):
            self.waves[i] = 0.0
        self.update()

    def update_animation(self):
        # Update each wave
        for i in range(self.wave_count):
            if self.waves[i] < 1.0:
                self.waves[i] += 0.05
            else:
                self.waves[i] = 0.0
        self.update()

    def paintEvent(self, event):
        if not self.is_animating:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        center_x = self.width() // 2
        center_y = self.height() // 2

        # Draw waves
        for i, scale in enumerate(self.waves):
            if scale > 0:
                opacity = 1.0 - scale
                if opacity < 0:
                    opacity = 0
                size = self.circle_radius * (1.0 + scale)

                painter.setPen(Qt.NoPen)
                color = self.wave_color  # Green color
                color.setAlphaF(opacity * 0.5)
                painter.setBrush(color)

                painter.drawEllipse(center_x - size, center_y - size, size * 2, size * 2)

        # Draw center circle
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.center_color)  # Yellow color
        painter.drawEllipse(center_x - self.circle_radius / 2, center_y - self.circle_radius / 2,
                            self.circle_radius, self.circle_radius)