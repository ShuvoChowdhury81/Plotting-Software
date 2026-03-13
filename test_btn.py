import sys
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout
from PyQt6.QtGui import QFont

app = QApplication(sys.argv)
app.setStyleSheet("""
    QWidget {
        font-family: "Segoe UI", "Open Sans", "Helvetica Neue", Arial, sans-serif;
        font-size: 13px;
        color: #334155;
    }
""")

w = QWidget()
l = QVBoxLayout(w)

b1 = QPushButton("B (QFont)")
f = b1.font()
f.setBold(True)
b1.setFont(f)
l.addWidget(b1)

b2 = QPushButton("B (css)")
b2.setStyleSheet("font-weight: bold;")
l.addWidget(b2)

w.show()
sys.exit(0)
