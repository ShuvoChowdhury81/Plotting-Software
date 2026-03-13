from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QRadioButton, QButtonGroup)
from PyQt6.QtCore import Qt

class AppendDataDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Data Already Exists")
        self.resize(350, 150)
        self.choice = "replace"
        
        layout = QVBoxLayout(self)
        
        lbl = QLabel("Data has already been loaded into the current frame. How would you like to handle the new data?")
        lbl.setWordWrap(True)
        layout.addWidget(lbl)
        
        layout.addSpacing(10)
        
        self.bg = QButtonGroup(self)
        
        self.rb_replace = QRadioButton("Replace existing data")
        self.rb_replace.setChecked(True)
        self.bg.addButton(self.rb_replace)
        layout.addWidget(self.rb_replace)
        
        self.rb_append = QRadioButton("Append data to active frame")
        self.bg.addButton(self.rb_append)
        layout.addWidget(self.rb_append)
        
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_ok = QPushButton("Ok")
        btn_ok.clicked.connect(self.accept)
        btn_ok.setDefault(True)
        btn_layout.addWidget(btn_ok)
        
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)
        
        layout.addLayout(btn_layout)

    def get_choice(self):
        if self.rb_append.isChecked():
            return "append"
        return "replace"
