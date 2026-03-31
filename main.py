import sys
import os
import traceback
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QIcon
from ui.main_window import FigaroApp


def global_exception_handler(exc_type, exc_value, exc_tb):
    """Catch unhandled exceptions and show them in a dialog instead of crashing."""
    # Don't intercept KeyboardInterrupt (Ctrl+C)
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_tb)
        return

    # Format the traceback
    tb_lines = traceback.format_exception(exc_type, exc_value, exc_tb)
    tb_text = "".join(tb_lines)

    # Print to console as well for debugging
    print(tb_text, file=sys.stderr)

    # Show error dialog
    try:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Figaro — Error")
        msg.setText(
            f"<b>An unexpected error occurred:</b><br><br>"
            f"<code>{exc_type.__name__}: {exc_value}</code>"
        )
        msg.setDetailedText(tb_text)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()
    except Exception:
        # If even the dialog fails, fall back to the default handler
        sys.__excepthook__(exc_type, exc_value, exc_tb)


if __name__ == "__main__":
    # Ensure Windows taskbar displays the app icon instead of the default Python icon
    try:
        import ctypes
        myappid = 'figaro.plotting.software.1.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

    app = QApplication(sys.argv)

    # Install global exception handler
    sys.excepthook = global_exception_handler

    # Set the global application icon
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.png")
    app.setWindowIcon(QIcon(icon_path))
    
    app.setStyle("Fusion") 
    window = FigaroApp()
    window.show()
    sys.exit(app.exec())
