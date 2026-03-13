import copy
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QComboBox, QGroupBox, QFormLayout, 
                             QDoubleSpinBox, QCheckBox, QWidget, QRadioButton, 
                             QButtonGroup)
from PyQt6.QtCore import Qt

class FrameSizePositionDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Frame Size & Position")
        self.resize(350, 400)
        self.parent_window = parent
        
        # Deepcopy the configuration
        if not hasattr(parent, 'frame_cfg'):
            parent.frame_cfg = {
                "paper_size": "Letter (8.5 x 11 in)",
                "orientation": "Portrait",
                "width": 6.0,
                "height": 6.0,
                "pos_x": 1.25,
                "pos_y": 2.5,
                "square_aspect": True,
                "show_border": True
            }
        self.cfg = copy.deepcopy(parent.frame_cfg)
        
        main_layout = QVBoxLayout(self)
        
        # --- Paper Setup ---
        grp_paper = QGroupBox("Paper Setup")
        form_paper = QFormLayout(grp_paper)
        
        self.cb_paper_size = QComboBox()
        self.cb_paper_size.addItems([
            "Letter (8.5 x 11 in)",
            "Legal (8.5 x 14 in)",
            "A4 (8.27 x 11.69 in)",
            "A3 (11.69 x 16.54 in)",
            "Custom"
        ])
        self.cb_paper_size.setCurrentText(self.cfg.get("paper_size", "Letter (8.5 x 11 in)"))
        self.cb_paper_size.currentTextChanged.connect(lambda t: self.update_cfg("paper_size", t))
        form_paper.addRow("Paper Size:", self.cb_paper_size)
        
        self.bg_orientation = QButtonGroup(self)
        self.rb_portrait = QRadioButton("Portrait")
        self.rb_landscape = QRadioButton("Landscape")
        self.bg_orientation.addButton(self.rb_portrait, 0)
        self.bg_orientation.addButton(self.rb_landscape, 1)
        
        hbox_orient = QHBoxLayout()
        hbox_orient.addWidget(self.rb_portrait)
        hbox_orient.addWidget(self.rb_landscape)
        form_paper.addRow("Orientation:", hbox_orient)
        
        if self.cfg.get("orientation", "Portrait") == "Landscape":
            self.rb_landscape.setChecked(True)
        else:
            self.rb_portrait.setChecked(True)
            
        self.bg_orientation.buttonClicked.connect(lambda b: self.update_cfg("orientation", b.text()))
        main_layout.addWidget(grp_paper)
        
        
        # --- Frame Size ---
        grp_size = QGroupBox("Frame Size & Position (inches)")
        form_size = QFormLayout(grp_size)
        
        self.sp_width = QDoubleSpinBox()
        self.sp_width.setRange(1.0, 50.0)
        self.sp_width.setSingleStep(0.5)
        self.sp_width.setValue(self.cfg.get("width", 6.0))
        self.sp_width.valueChanged.connect(self._on_width_changed)
        form_size.addRow("Width:", self.sp_width)
        
        self.sp_height = QDoubleSpinBox()
        self.sp_height.setRange(1.0, 50.0)
        self.sp_height.setSingleStep(0.5)
        self.sp_height.setValue(self.cfg.get("height", 6.0))
        self.sp_height.valueChanged.connect(self._on_height_changed)
        form_size.addRow("Height:", self.sp_height)
        
        self.chk_square = QCheckBox("Force Square Plot Area (1:1 Aspect Ratio)")
        self.chk_square.setChecked(self.cfg.get("square_aspect", True))
        self.chk_square.stateChanged.connect(self._on_square_toggled)
        form_size.addRow("", self.chk_square)
        
        # Position 
        self.sp_pos_x = QDoubleSpinBox()
        self.sp_pos_x.setRange(0.0, 50.0)
        self.sp_pos_x.setSingleStep(0.25)
        self.sp_pos_x.setValue(self.cfg.get("pos_x", 1.25))
        self.sp_pos_x.valueChanged.connect(lambda v: self.update_cfg("pos_x", v))
        form_size.addRow("X-Position:", self.sp_pos_x)
        
        self.sp_pos_y = QDoubleSpinBox()
        self.sp_pos_y.setRange(0.0, 50.0)
        self.sp_pos_y.setSingleStep(0.25)
        self.sp_pos_y.setValue(self.cfg.get("pos_y", 2.5))
        self.sp_pos_y.valueChanged.connect(lambda v: self.update_cfg("pos_y", v))
        form_size.addRow("Y-Position:", self.sp_pos_y)
        
        self.chk_border = QCheckBox("Show Frame Border")
        self.chk_border.setChecked(self.cfg.get("show_border", True))
        self.chk_border.stateChanged.connect(lambda s: self.update_cfg("show_border", s == Qt.CheckState.Checked.value))
        form_size.addRow("", self.chk_border)
        
        main_layout.addWidget(grp_size)
        main_layout.addStretch()
        
        # --- Bottom Dialog buttons ---
        bottom_hbox = QHBoxLayout()
        bottom_hbox.addStretch()
        
        btn_apply = QPushButton("Apply")
        btn_apply.clicked.connect(self.apply_changes)
        bottom_hbox.addWidget(btn_apply)

        btn_ok = QPushButton("Ok")
        btn_ok.clicked.connect(self.accept_changes)
        btn_ok.setDefault(True)
        bottom_hbox.addWidget(btn_ok)
        
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.close)
        bottom_hbox.addWidget(btn_close)
        
        main_layout.addLayout(bottom_hbox)
        
        # Initialize sync
        self._on_square_toggled(self.chk_square.checkState().value)

    def _on_square_toggled(self, state):
        is_checked = (state == Qt.CheckState.Checked.value)
        self.update_cfg("square_aspect", is_checked)
        if is_checked:
            # Sync height to width
            self.sp_height.setValue(self.sp_width.value())
            
    def _on_width_changed(self, val):
        self.update_cfg("width", val)
        if self.chk_square.isChecked():
            self.sp_height.blockSignals(True)
            self.sp_height.setValue(val)
            self.update_cfg("height", val)
            self.sp_height.blockSignals(False)
            
    def _on_height_changed(self, val):
        self.update_cfg("height", val)
        if self.chk_square.isChecked():
            self.sp_width.blockSignals(True)
            self.sp_width.setValue(val)
            self.update_cfg("width", val)
            self.sp_width.blockSignals(False)

    def update_cfg(self, key, value):
        self.cfg[key] = value

    def apply_changes(self):
        self.parent_window.frame_cfg = copy.deepcopy(self.cfg)
        self.parent_window.update_plot()
        
    def accept_changes(self):
        self.apply_changes()
        self.close()
