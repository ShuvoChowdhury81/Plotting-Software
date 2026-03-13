import sys
from PyQt6.QtWidgets import QApplication, QWidget, QCheckBox, QVBoxLayout

app = QApplication(sys.argv)
window = QWidget()
layout = QVBoxLayout(window)

cb = QCheckBox("Test Box")
cb.setChecked(True)
layout.addWidget(cb)

# The stylesheet from main.py
window.setStyleSheet("""
    QCheckBox::indicator {
        width: 16px;
        height: 16px;
        border-radius: 0px;
        background-color: #ffffff;
        border: 1px solid #757575;
    }
    QCheckBox::indicator:checked {
        background-color: #ffffff;
        border: 1px solid #424242;
        image: url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAABTSURBVDhPYxzBQAQMxP/pZg+2AhiI1Y5VA2bEWMDEyMT0H8wmg1E1kG0AzRykBgBdgOw2ZAF0A7EahDQAYiL1AKMBtHSAkQFIQzQpAA2hB5gYGAA/VxE/sTj2lwAAAABJRU5ErkJggg==);
    }
""")

window.show()
sys.exit(app.exec())
