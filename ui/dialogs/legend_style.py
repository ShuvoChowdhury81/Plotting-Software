import sys
import copy
import numpy as np
from scipy import interpolate
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QComboBox, 
                             QColorDialog, QFileDialog, QGroupBox, QSpinBox,
                             QFormLayout, QMenuBar, QMenu, QToolBar, QDockWidget,
                             QTabWidget, QStatusBar, QSpacerItem, QSizePolicy,
                             QDialog, QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox,
                             QRadioButton, QButtonGroup, QDoubleSpinBox, QLineEdit)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction, QIcon, QColor, QFont


class LegendDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Legend")
        self.resize(320, 480)
        self.parent_window = parent
        self.cfg = copy.deepcopy(parent.legend_cfg)
        
        layout = QVBoxLayout(self)
        
        # Checkboxes
        self.chk_show = QCheckBox("Show Line Legend")
        self.chk_show.setChecked(self.cfg.get("show_line_legend", True))
        self.chk_show.stateChanged.connect(lambda s: self.update_cfg("show_line_legend", s == Qt.CheckState.Checked.value))
        layout.addWidget(self.chk_show)
        
        self.chk_names = QCheckBox("Show Mapping Names")
        self.chk_names.setChecked(self.cfg.get("show_mapping_names", True))
        self.chk_names.stateChanged.connect(lambda s: self.update_cfg("show_mapping_names", s == Qt.CheckState.Checked.value))
        layout.addWidget(self.chk_names)
        
        # Text Group
        grp_text = QGroupBox("Text")
        l_text = QFormLayout(grp_text)
        
        hbox_font = QHBoxLayout()
        self.cb_font = QComboBox()
        self.cb_font.addItems(["STIXGeneral", "DejaVu Serif", "Times New Roman", "Courier", "Arial"])
        self.cb_font.setCurrentText(self.cfg.get("font", "STIXGeneral"))
        self.cb_font.currentTextChanged.connect(lambda t: self.update_cfg("font", t))
        hbox_font.addWidget(self.cb_font)
        
        self.btn_bold = QPushButton("B")
        self.btn_bold.setCheckable(True)
        self.btn_bold.setFixedWidth(36)
        self.btn_bold.setStyleSheet("font-weight: bold; padding: 0px;")
        self.btn_bold.setChecked(self.cfg.get("bold", False))
        self.btn_bold.toggled.connect(lambda s: self.update_cfg("bold", s))
        hbox_font.addWidget(self.btn_bold)
        
        self.btn_italic = QPushButton("I")
        self.btn_italic.setCheckable(True)
        self.btn_italic.setFixedWidth(36)
        self.btn_italic.setStyleSheet("font-style: italic; padding: 0px;")
        self.btn_italic.setChecked(self.cfg.get("italic", False))
        self.btn_italic.toggled.connect(lambda s: self.update_cfg("italic", s))
        hbox_font.addWidget(self.btn_italic)
        l_text.addRow("Font:", hbox_font)
        
        hbox_size = QHBoxLayout()
        self.sp_size = QSpinBox()
        self.sp_size.setRange(1, 50)
        self.sp_size.setValue(self.cfg.get("size", 10))
        self.sp_size.valueChanged.connect(lambda v: self.update_cfg("size", v))
        hbox_size.addWidget(self.sp_size)
        
        cb_frame = QComboBox()
        cb_frame.addItems(["Frame%", "Point"])
        hbox_size.addWidget(cb_frame)
        
        self.btn_txt_color = QPushButton("Color")
        self.set_color_button_style(self.btn_txt_color, self.cfg.get('text_color', '#000000'))
        self.btn_txt_color.clicked.connect(lambda: self.pick_color("text_color", self.btn_txt_color))
        hbox_size.addWidget(self.btn_txt_color)
        l_text.addRow("Size:", hbox_size)
        
        layout.addWidget(grp_text)
        
        # Position Group
        grp_pos = QGroupBox("Position")
        l_pos = QFormLayout(grp_pos)
        
        self.le_x = QLineEdit(str(self.cfg.get("pos_x", 95)))
        self.le_x.textChanged.connect(lambda t: self.update_cfg("pos_x", float(t) if t else 95))
        l_pos.addRow("X (%):", self.le_x)
        
        self.le_y = QLineEdit(str(self.cfg.get("pos_y", 80)))
        self.le_y.textChanged.connect(lambda t: self.update_cfg("pos_y", float(t) if t else 80))
        l_pos.addRow("Y (%):", self.le_y)
        
        self.le_spacing = QLineEdit(str(self.cfg.get("line_spacing", 1.2)))
        self.le_spacing.textChanged.connect(lambda t: self.update_cfg("line_spacing", float(t) if t else 1.2))
        l_pos.addRow("Line spacing:", self.le_spacing)
        layout.addWidget(grp_pos)
        
        # Legend box Group
        grp_box = QGroupBox("Legend box")
        l_box = QFormLayout(grp_box)
        
        hbox_radios = QHBoxLayout()
        self.bg_box = QButtonGroup(self)
        for i, lbl in enumerate(["No box", "Outline", "Fill"]):
            rb = QRadioButton(lbl)
            self.bg_box.addButton(rb, i)
            hbox_radios.addWidget(rb)
            if self.cfg.get("box_type", "Outline") == lbl:
                rb.setChecked(True)
        self.bg_box.buttonClicked.connect(lambda btn: self.update_cfg("box_type", btn.text()))
        l_box.addRow("", hbox_radios)
        
        self.cb_thick = QComboBox()
        self.cb_thick.addItems(["0.1", "0.2", "0.4", "0.8"])
        self.cb_thick.setCurrentText(self.cfg.get("box_line_thickness", "0.1"))
        self.cb_thick.currentTextChanged.connect(lambda t: self.update_cfg("box_line_thickness", t))
        l_box.addRow("Line thickness (%):", self.cb_thick)
        
        self.btn_box_color = QPushButton("Color")
        self.set_color_button_style(self.btn_box_color, self.cfg.get('box_color', '#000000'))
        self.btn_box_color.clicked.connect(lambda: self.pick_color("box_color", self.btn_box_color))
        l_box.addRow("Box color:", self.btn_box_color)
        
        self.btn_fill_color = QPushButton("Color")
        self.set_color_button_style(self.btn_fill_color, self.cfg.get('fill_color', '#ffffff'))
        self.btn_fill_color.clicked.connect(lambda: self.pick_color("fill_color", self.btn_fill_color))
        l_box.addRow("Fill color:", self.btn_fill_color)
        
        self.sp_margin = QSpinBox()
        self.sp_margin.setRange(0, 50)
        self.sp_margin.setValue(self.cfg.get("margin", 10))
        self.sp_margin.valueChanged.connect(lambda v: self.update_cfg("margin", v))
        l_box.addRow("Margin:", self.sp_margin)
        layout.addWidget(grp_box)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_apply = QPushButton("Apply")
        btn_apply.clicked.connect(self.apply_changes)
        btn_layout.addWidget(btn_apply)

        btn_ok = QPushButton("Ok")
        btn_ok.clicked.connect(self.accept_changes)
        btn_ok.setDefault(True)
        btn_layout.addWidget(btn_ok)
        
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.close)
        btn_layout.addWidget(btn_close)
        
        layout.addLayout(btn_layout)
        
    def update_cfg(self, key, value):
        self.cfg[key] = value
        
    def apply_changes(self):
        self.parent_window.legend_cfg.update(self.cfg)
        self.parent_window.update_plot()
        
    def accept_changes(self):
        self.apply_changes()
        self.close()
        
    def set_color_button_style(self, btn, color_hex):
        color = QColor(color_hex)
        lum = color.lightness()
        txt_col = "black" if lum > 128 else "white"
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color_hex};
                color: {txt_col};
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                padding: 4px 12px;
            }}
        """)

    def pick_color(self, key, btn):
        color = QColorDialog.getColor()
        if color.isValid():
            self.update_cfg(key, color.name())
            self.set_color_button_style(btn, color.name())

