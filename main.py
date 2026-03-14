import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import FigaroApp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion") 
    window = FigaroApp()
    window.show()
    sys.exit(app.exec())
