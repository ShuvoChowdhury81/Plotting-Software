from PyQt6.QtCore import Qt, QRectF, QPropertyAnimation, pyqtProperty, QEasingCurve, QPoint, QSize
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtWidgets import QCheckBox

class SwitchButton(QCheckBox):
    def __init__(self, text="", parent=None, bg_color="#CCCCCC", circle_color="#FFFFFF", active_color="#006FCC"):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._bg_color = bg_color
        self._circle_color = circle_color
        self._active_color = active_color

        self._position = 1.0 if self.isChecked() else 0.0
        self.animation = QPropertyAnimation(self, b"position")
        self.animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        self.animation.setDuration(150)

        self.stateChanged.connect(self.setup_animation)

    @pyqtProperty(float)
    def position(self):
        return self._position

    @position.setter
    def position(self, pos):
        self._position = pos
        self.update()

    def setup_animation(self, value):
        self.animation.stop()
        if value:
            self.animation.setEndValue(1.0)
        else:
            self.animation.setEndValue(0.0)
        self.animation.start()

    def hitButton(self, pos: QPoint):
        return self.contentsRect().contains(pos)

    def sizeHint(self):
        hint = super().sizeHint()
        # Add width to accommodate the switch pill (36px) plus spacing (8px)
        hint.setWidth(hint.width() + 44)
        return QSize(hint.width(), max(hint.height(), 20))

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        switch_width = 36
        switch_height = 20
        
        # Vertical alignment
        y_offset = (self.height() - switch_height) // 2
        
        p.setPen(Qt.PenStyle.NoPen)

        # Draw pill background
        if not self.isChecked():
            p.setBrush(QColor(self._bg_color))
        else:
            p.setBrush(QColor(self._active_color))
            
        p.drawRoundedRect(0, y_offset, switch_width, switch_height, switch_height / 2.0, switch_height / 2.0)

        # Draw white thumb slider
        p.setBrush(QColor(self._circle_color))
        circle_radius = switch_height - 4
        circle_x = 2 + self._position * (switch_width - circle_radius - 4)
        p.drawEllipse(int(circle_x), int(y_offset + 2), int(circle_radius), int(circle_radius))
        
        # Draw label string correctly aligned next to the switch
        if self.text():
            p.setPen(QColor("#000000"))
            text_rect = QRectF(switch_width + 8, 0, self.width() - switch_width - 8, self.height())
            p.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self.text())
        
        p.end()
