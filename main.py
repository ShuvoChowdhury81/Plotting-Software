import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from ui.main_window import FigaroApp

if __name__ == "__main__":
    # Ensure Windows taskbar displays the app icon instead of the default Python icon
    try:
        import ctypes
        myappid = 'figaro.plotting.software.1.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

    app = QApplication(sys.argv)
    
    # Set the global application icon
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.png")
    app.setWindowIcon(QIcon(icon_path))
    
    app.setStyle("Fusion") 
    window = FigaroApp()
    window.show()
    sys.exit(app.exec())
