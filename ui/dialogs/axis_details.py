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
                             QRadioButton, QButtonGroup, QDoubleSpinBox, QLineEdit, QFrame)
from PyQt6.QtCore import Qt, QSize
from ui.widgets.switch import SwitchButton
from PyQt6.QtGui import QAction, QIcon, QColor, QFont, QPixmap


class AxisDetailsDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Axis Details")
        self.resize(650, 450)
        self.parent_window = parent
        self.cfg = copy.deepcopy(parent.axis_cfg)
        
        self.current_axis = "X1"
        
        main_layout = QVBoxLayout(self)
        
        # Top Row
        top_hbox = QHBoxLayout()
        self.chk_show_axis = SwitchButton(f"Show {self.current_axis}-Axis")
        self.chk_show_axis.setChecked(self.cfg.get(f"{self.current_axis}_show", True))
        self.chk_show_axis.stateChanged.connect(lambda s: self.update_cfg(f"{self.current_axis}_show", s == Qt.CheckState.Checked.value))
        top_hbox.addWidget(self.chk_show_axis)
        
        top_hbox.addSpacing(20)
        
        self.axis_group = QButtonGroup(self)
        axes_names = ["X1", "Y1", "X2", "Y2", "X3", "Y3", "X4", "Y4", "X5", "Y5"]
        for i, name in enumerate(axes_names):
            btn = QPushButton(name)
            btn.setCheckable(True)
            if name == "X1": btn.setChecked(True)
            self.axis_group.addButton(btn, i)
            top_hbox.addWidget(btn)
        
        self.axis_group.buttonClicked.connect(self.on_axis_changed)
        
        top_hbox.addStretch()
        main_layout.addLayout(top_hbox)
        
        # Tabs
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        self.tab_range = QWidget()
        self.tabs.addTab(self.tab_range, "Range")
        
        self.tab_grid = QWidget()
        self.tabs.addTab(self.tab_grid, "Grid")
        
        self.tab_ticks = QWidget()
        self.tabs.addTab(self.tab_ticks, "Ticks")
        
        self.tab_labels = QWidget()
        self.tabs.addTab(self.tab_labels, "Labels")
        
        self.tab_title = QWidget()
        self.tabs.addTab(self.tab_title, "Title")
        
        self.tab_line = QWidget()
        self.tabs.addTab(self.tab_line, "Line")
        
        self.tabs.addTab(QWidget(), "Area")
        
        self.setup_range_tab()
        self.setup_grid_tab()
        self.setup_ticks_tab()
        self.setup_labels_tab()
        self.setup_title_tab()
        self.setup_line_tab()
        
        # Bottom Dialog buttons
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
        
    def apply_changes(self):
        self.update_min_max("min", self.le_min.text())
        self.update_min_max("max", self.le_max.text())
        self.parent_window.axis_cfg.update(self.cfg)
        self.parent_window.update_plot()
        
    def accept_changes(self):
        self.apply_changes()
        self.close()

    def setup_range_tab(self):
        layout = QVBoxLayout(self.tab_range)
        
        # Min/Max Group
        min_max_layout = QFormLayout()
        
        hbox_min = QHBoxLayout()
        self.le_min = QLineEdit()
        self.le_min.setFixedWidth(150)
        # Parse Matplotlib limits instead of dict if available
        lims = self.parent_window.ax.get_xlim()
        self.le_min.setText(str(round(lims[0], 4)))
        self.le_min.editingFinished.connect(lambda: self.update_min_max("min", self.le_min.text()))
        hbox_min.addWidget(self.le_min)
        
        btn_reset = QPushButton("Reset Range")
        btn_reset.clicked.connect(self.reset_range)
        hbox_min.addWidget(btn_reset)
        hbox_min.addStretch()
        min_max_layout.addRow("Min:", hbox_min)
        
        self.le_max = QLineEdit()
        self.le_max.setFixedWidth(150)
        self.le_max.setText(str(round(lims[1], 4)))
        self.le_max.editingFinished.connect(lambda: self.update_min_max("max", self.le_max.text()))
        min_max_layout.addRow("Max:", self.le_max)
        
        layout.addLayout(min_max_layout)
        
        # Checkboxes
        grid_chk = QFormLayout()
        
        self.chk_nice_fit = QCheckBox("Automatically adjust to nice values")
        self.chk_nice_fit.setChecked(self.cfg.get("nice_fit", False))
        self.chk_nice_fit.stateChanged.connect(self._on_nice_fit_changed)
        layout.addWidget(self.chk_nice_fit)
        
        self.chk_preserve = QCheckBox("Preserve axis length when changing range")
        self.chk_preserve.setChecked(self.cfg.get(f"{self.current_axis}_preserve", True))
        self.chk_preserve.stateChanged.connect(lambda s: self.update_cfg(f"{self.current_axis}_preserve", s == Qt.CheckState.Checked.value))
        
        self.chk_log = QCheckBox("Use log scale")
        self.chk_log.setChecked(self.cfg.get(f"{self.current_axis}_log", False))
        self.chk_log.stateChanged.connect(lambda s: self.update_cfg(f"{self.current_axis}_log", s == Qt.CheckState.Checked.value))
        
        self.chk_reverse = QCheckBox("Reverse axis direction")
        self.chk_reverse.setChecked(self.cfg.get(f"{self.current_axis}_reverse", False))
        self.chk_reverse.stateChanged.connect(lambda s: self.update_cfg(f"{self.current_axis}_reverse", s == Qt.CheckState.Checked.value))
        
        # Custom mini layout for two-column checkboxes
        h1 = QHBoxLayout()
        h1.addWidget(self.chk_preserve)
        h1.addWidget(self.chk_log)
        layout.addLayout(h1)
        layout.addWidget(self.chk_reverse)
        
        # Dependency Group
        grp_dep = QGroupBox("Dependency")
        l_dep = QVBoxLayout(grp_dep)
        
        h_dep = QHBoxLayout()
        self.bg_dep = QButtonGroup(self)
        rb_dep = QRadioButton("Dependent")
        rb_indep = QRadioButton("Independent")
        self.bg_dep.addButton(rb_dep, 0)
        self.bg_dep.addButton(rb_indep, 1)
        
        if self.cfg.get(f"{self.current_axis}_dep", "Independent") == "Dependent":
            rb_dep.setChecked(True)
        else:
            rb_indep.setChecked(True)
            
        self.bg_dep.buttonClicked.connect(lambda b: self.update_cfg(f"{self.current_axis}_dep", b.text()))
        
        h_dep.addWidget(rb_dep)
        self.lbl_ratio = QLabel("X to Y ratio:")
        self.le_ratio = QLineEdit("1")
        self.le_ratio.setFixedWidth(80)
        self.le_ratio.setEnabled(rb_dep.isChecked())
        h_dep.addWidget(self.lbl_ratio)
        h_dep.addWidget(self.le_ratio)
        h_dep.addStretch()
        l_dep.addLayout(h_dep)
        l_dep.addWidget(rb_indep)
        
        # Wire toggle dependency
        rb_dep.toggled.connect(self.le_ratio.setEnabled)
        
        layout.addWidget(grp_dep)
        layout.addStretch()

    def setup_grid_tab(self):
        outer = QVBoxLayout(self.tab_grid)
        
        # Gridlines and Minor Gridlines (Columns)
        h_cols = QHBoxLayout()
        
        # ── LEFT COL: Gridlines ──────────────────────────────────────────────
        v_left = QVBoxLayout()
        # Header Label (no bold)
        lbl_grid = QLabel("Gridlines")
        v_left.addWidget(lbl_grid)
        
        # Show checkbox
        self.chk_grid_show = QCheckBox("Show")
        self.chk_grid_show.setChecked(self.cfg.get(f"{self.current_axis}_grid_show", True))
        self.chk_grid_show.stateChanged.connect(lambda s: self.update_cfg(f"{self.current_axis}_grid_show", s == Qt.CheckState.Checked.value))
        v_left.addWidget(self.chk_grid_show)
        
        form_left = QFormLayout()
        form_left.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        # Line pattern
        self.cb_grid_pattern = QComboBox()
        self.cb_grid_pattern.addItems(["Solid", "Dashed", "DashDot", "Dotted"])
        self.cb_grid_pattern.setCurrentText(self.cfg.get(f"{self.current_axis}_grid_pattern", "Solid"))
        self.cb_grid_pattern.currentTextChanged.connect(lambda t: self.update_cfg(f"{self.current_axis}_grid_pattern", t))
        form_left.addRow("Line pattern:", self.cb_grid_pattern)
        
        # Pattern length (%)
        self.le_grid_len = QLineEdit(str(self.cfg.get(f"{self.current_axis}_grid_len", 2)))
        self.le_grid_len.editingFinished.connect(lambda: self._apply_grid_value("grid_len", self.le_grid_len.text()))
        form_left.addRow("Pattern length (%):", self.le_grid_len)
        
        # Thickness (%)
        self.cb_grid_thick = QComboBox()
        self.cb_grid_thick.addItems(["0.1", "0.2", "0.4", "0.8"])
        self.cb_grid_thick.setCurrentText(str(self.cfg.get(f"{self.current_axis}_grid_thick", 0.1)))
        self.cb_grid_thick.setEditable(True)
        self.cb_grid_thick.currentTextChanged.connect(lambda t: self.update_cfg(f"{self.current_axis}_grid_thick", t))
        form_left.addRow("Thickness (%):", self.cb_grid_thick)
        
        # Gridline color
        self._grid_color = QColor(self.cfg.get(f"{self.current_axis}_grid_color", "#000000"))
        self.btn_grid_color = QPushButton()
        self.btn_grid_color.setFixedWidth(80)
        self._update_color_btn(self.btn_grid_color, self._grid_color)
        self.btn_grid_color.clicked.connect(lambda: self._pick_color("_grid_color", self.btn_grid_color, f"{self.current_axis}_grid_color"))
        form_left.addRow("Gridline color:", self.btn_grid_color)
        
        # Draw order
        self.cb_grid_order = QComboBox()
        self.cb_grid_order.addItems(["First", "Last"])
        self.cb_grid_order.setCurrentText(self.cfg.get(f"{self.current_axis}_grid_order", "First"))
        self.cb_grid_order.currentTextChanged.connect(lambda t: self.update_cfg(f"{self.current_axis}_grid_order", t))
        form_left.addRow("Gridline draw order:", self.cb_grid_order)
        
        v_left.addLayout(form_left)
        v_left.addStretch()
        h_cols.addLayout(v_left)
        
        # ── RIGHT COL: Minor gridlines ───────────────────────────────────────
        v_right = QVBoxLayout()
        # Header Label (no bold)
        lbl_minor = QLabel("Minor gridlines")
        v_right.addWidget(lbl_minor)
        
        # Show checkbox
        self.chk_minor_grid_show = QCheckBox("Show")
        self.chk_minor_grid_show.setChecked(self.cfg.get(f"{self.current_axis}_minor_grid_show", False))
        self.chk_minor_grid_show.stateChanged.connect(lambda s: self.update_cfg(f"{self.current_axis}_minor_grid_show", s == Qt.CheckState.Checked.value))
        v_right.addWidget(self.chk_minor_grid_show)
        
        form_right = QFormLayout()
        form_right.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        # Line pattern (Right side aligns with right side elements but no label text based on image)
        # But image shows empty space where labels would be, so we use dummy labels.
        self.cb_minor_grid_pattern = QComboBox()
        self.cb_minor_grid_pattern.addItems(["Solid", "Dashed", "DashDot", "Dotted"])
        self.cb_minor_grid_pattern.setCurrentText(self.cfg.get(f"{self.current_axis}_minor_grid_pattern", "Dotted"))
        self.cb_minor_grid_pattern.currentTextChanged.connect(lambda t: self.update_cfg(f"{self.current_axis}_minor_grid_pattern", t))
        form_right.addRow(QLabel(" "), self.cb_minor_grid_pattern) 
        
        # Pattern length (%)
        self.le_minor_grid_len = QLineEdit(str(self.cfg.get(f"{self.current_axis}_minor_grid_len", 2)))
        self.le_minor_grid_len.editingFinished.connect(lambda: self._apply_grid_value("minor_grid_len", self.le_minor_grid_len.text()))
        form_right.addRow(QLabel(" "), self.le_minor_grid_len)
        
        # Thickness (%)
        self.cb_minor_grid_thick = QComboBox()
        self.cb_minor_grid_thick.addItems(["0.1", "0.2", "0.4", "0.8"])
        self.cb_minor_grid_thick.setCurrentText(str(self.cfg.get(f"{self.current_axis}_minor_grid_thick", 0.1)))
        self.cb_minor_grid_thick.setEditable(True)
        self.cb_minor_grid_thick.currentTextChanged.connect(lambda t: self.update_cfg(f"{self.current_axis}_minor_grid_thick", t))
        form_right.addRow(QLabel(" "), self.cb_minor_grid_thick)
        
        # Gridline color
        self._minor_grid_color = QColor(self.cfg.get(f"{self.current_axis}_minor_grid_color", "#000000"))
        self.btn_minor_grid_color = QPushButton()
        self.btn_minor_grid_color.setFixedWidth(80)
        self._update_color_btn(self.btn_minor_grid_color, self._minor_grid_color)
        self.btn_minor_grid_color.clicked.connect(lambda: self._pick_color("_minor_grid_color", self.btn_minor_grid_color, f"{self.current_axis}_minor_grid_color"))
        form_right.addRow(QLabel(" "), self.btn_minor_grid_color)
        
        # Draw order
        self.cb_minor_grid_order = QComboBox()
        self.cb_minor_grid_order.addItems(["First", "Last"])
        self.cb_minor_grid_order.setCurrentText(self.cfg.get(f"{self.current_axis}_minor_grid_order", "First"))
        self.cb_minor_grid_order.currentTextChanged.connect(lambda t: self.update_cfg(f"{self.current_axis}_minor_grid_order", t))
        form_right.addRow(QLabel(" "), self.cb_minor_grid_order)
        
        v_right.addLayout(form_right)
        v_right.addStretch()
        h_cols.addLayout(v_right)
        
        outer.addLayout(h_cols)
        
        # Toggle mechanics
        self.chk_minor_grid_show.toggled.connect(self.cb_minor_grid_pattern.setEnabled)
        self.chk_minor_grid_show.toggled.connect(self.le_minor_grid_len.setEnabled)
        self.chk_minor_grid_show.toggled.connect(self.cb_minor_grid_thick.setEnabled)
        self.chk_minor_grid_show.toggled.connect(self.btn_minor_grid_color.setEnabled)
        self.chk_minor_grid_show.toggled.connect(self.cb_minor_grid_order.setEnabled)
        
        self.cb_minor_grid_pattern.setEnabled(self.chk_minor_grid_show.isChecked())
        self.le_minor_grid_len.setEnabled(self.chk_minor_grid_show.isChecked())
        self.cb_minor_grid_thick.setEnabled(self.chk_minor_grid_show.isChecked())
        self.btn_minor_grid_color.setEnabled(self.chk_minor_grid_show.isChecked())
        self.cb_minor_grid_order.setEnabled(self.chk_minor_grid_show.isChecked())
        
        outer.addSpacing(20)
        
        # Bottom: Show precise dot grid
        self.chk_dot_grid = QCheckBox("Show precise dot grid")
        self.chk_dot_grid.setChecked(self.cfg.get(f"{self.current_axis}_dot_grid", False))
        self.chk_dot_grid.stateChanged.connect(lambda s: self.update_cfg(f"{self.current_axis}_dot_grid", s == Qt.CheckState.Checked.value))
        outer.addWidget(self.chk_dot_grid)
        
        bottom_h = QHBoxLayout()
        bottom_h.setContentsMargins(20, 0, 0, 0)
        bottom_h.addWidget(QLabel("Dot size (cm):"))
        self.le_dot_size = QLineEdit(str(self.cfg.get(f"{self.current_axis}_dot_size", 0.0045)))
        self.le_dot_size.setFixedWidth(80)
        bottom_h.addWidget(self.le_dot_size)
        
        bottom_h.addSpacing(20)
        bottom_h.addWidget(QLabel("Dot color:"))
        self._dot_color = QColor(self.cfg.get(f"{self.current_axis}_dot_color", "#000000"))
        self.btn_dot_color = QPushButton()
        self.btn_dot_color.setFixedWidth(80)
        self._update_color_btn(self.btn_dot_color, self._dot_color)
        self.btn_dot_color.clicked.connect(lambda: self._pick_color("_dot_color", self.btn_dot_color, f"{self.current_axis}_dot_color"))
        bottom_h.addWidget(self.btn_dot_color)
        
        bottom_h.addStretch()
        outer.addLayout(bottom_h)
        
        self.chk_dot_grid.toggled.connect(self.le_dot_size.setEnabled)
        self.chk_dot_grid.toggled.connect(self.btn_dot_color.setEnabled)
        self.le_dot_size.setEnabled(self.chk_dot_grid.isChecked())
        self.btn_dot_color.setEnabled(self.chk_dot_grid.isChecked())

    def setup_ticks_tab(self):
        layout = QVBoxLayout(self.tab_ticks)
        
        # --- Major Ticks Section ---
        grp_major = QGroupBox("Major Ticks")
        l_major = QVBoxLayout(grp_major)
        
        h_major_top = QHBoxLayout()
        self.chk_show_ticks = QCheckBox("Show Ticks")
        self.chk_show_ticks.setChecked(self.cfg.get(f"{self.current_axis}_show_ticks", True))
        self.chk_show_ticks.stateChanged.connect(lambda s: self.update_cfg(f"{self.current_axis}_show_ticks", s == Qt.CheckState.Checked.value))
        
        h_major_top.addWidget(self.chk_show_ticks)
        h_major_top.addStretch()
        l_major.addLayout(h_major_top)
        
        # Tick Direction
        h_dir = QHBoxLayout()
        h_dir.addWidget(QLabel("Tick Direction:"))
        self.cb_tick_dir = QComboBox()
        self.cb_tick_dir.addItems(["In", "Out", "Both"])
        self.cb_tick_dir.setCurrentText(self.cfg.get(f"{self.current_axis}_tick_dir", "Out").capitalize())
        self.cb_tick_dir.currentTextChanged.connect(lambda t: self.update_cfg(f"{self.current_axis}_tick_dir", t.lower()))
        h_dir.addWidget(self.cb_tick_dir)
        h_dir.addStretch()
        l_major.addLayout(h_dir)
        
        # Tick Size/Length
        h_size = QHBoxLayout()
        h_size.addWidget(QLabel("Length:"))
        self.sp_tick_len = QDoubleSpinBox()
        self.sp_tick_len.setRange(1.0, 20.0)
        self.sp_tick_len.setValue(self.cfg.get(f"{self.current_axis}_tick_len", 4.0))
        self.sp_tick_len.valueChanged.connect(lambda v: self.update_cfg(f"{self.current_axis}_tick_len", v))
        h_size.addWidget(self.sp_tick_len)
        
        h_size.addSpacing(20)
        h_size.addWidget(QLabel("Thickness:"))
        self.sp_tick_width = QDoubleSpinBox()
        self.sp_tick_width.setRange(0.1, 5.0)
        self.sp_tick_width.setSingleStep(0.1)
        self.sp_tick_width.setValue(self.cfg.get(f"{self.current_axis}_tick_width", 1.0))
        self.sp_tick_width.valueChanged.connect(lambda v: self.update_cfg(f"{self.current_axis}_tick_width", v))
        h_size.addWidget(self.sp_tick_width)
        h_size.addStretch()
        l_major.addLayout(h_size)
        
        layout.addWidget(grp_major)
        
        # --- Minor Ticks Section ---
        grp_minor = QGroupBox("Minor Ticks")
        l_minor = QVBoxLayout(grp_minor)
        
        self.chk_show_minor_ticks = QCheckBox("Show Minor Ticks")
        self.chk_show_minor_ticks.setChecked(self.cfg.get(f"{self.current_axis}_show_minor_ticks", False))
        self.chk_show_minor_ticks.stateChanged.connect(lambda s: self.update_cfg(f"{self.current_axis}_show_minor_ticks", s == Qt.CheckState.Checked.value))
        l_minor.addWidget(self.chk_show_minor_ticks)
        
        h_minor_size = QHBoxLayout()
        h_minor_size.addWidget(QLabel("Length:"))
        self.sp_minor_tick_len = QDoubleSpinBox()
        self.sp_minor_tick_len.setRange(1.0, 15.0)
        self.sp_minor_tick_len.setValue(self.cfg.get(f"{self.current_axis}_minor_tick_len", 2.0))
        self.sp_minor_tick_len.valueChanged.connect(lambda v: self.update_cfg(f"{self.current_axis}_minor_tick_len", v))
        h_minor_size.addWidget(self.sp_minor_tick_len)
        h_minor_size.addStretch()
        l_minor.addLayout(h_minor_size)
        
        layout.addWidget(grp_minor)
        
        # --- Tick Marks and Label Spacing ---
        grp_spacing = QGroupBox("Tick marks and label spacing")
        l_spacing = QHBoxLayout(grp_spacing)
        
        self.chk_auto_spacing = QCheckBox("Auto spacing")
        self.chk_auto_spacing.setChecked(self.cfg.get(f"{self.current_axis}_auto_spacing", True))
        self.chk_auto_spacing.stateChanged.connect(lambda s: self.update_cfg(f"{self.current_axis}_auto_spacing", s == Qt.CheckState.Checked.value))
        l_spacing.addWidget(self.chk_auto_spacing)
        
        l_spacing.addSpacing(10)
        l_spacing.addWidget(QLabel("Spacing:"))
        self.sp_spacing = QDoubleSpinBox()
        self.sp_spacing.setRange(0.001, 1000000.0)
        self.sp_spacing.setDecimals(3)
        self.sp_spacing.setValue(self.cfg.get(f"{self.current_axis}_spacing", 30.0))
        self.sp_spacing.setEnabled(not self.chk_auto_spacing.isChecked())
        self.sp_spacing.valueChanged.connect(lambda v: self.update_cfg(f"{self.current_axis}_spacing", v))
        l_spacing.addWidget(self.sp_spacing)
        
        # Tie checkbox to spinbox enabled state
        self.chk_auto_spacing.toggled.connect(lambda checked: self.sp_spacing.setEnabled(not checked))
        
        l_spacing.addStretch()
        layout.addWidget(grp_spacing)
        
        layout.addStretch()
        
    def setup_labels_tab(self):
        outer = QVBoxLayout(self.tab_labels)

        # ── Main content area (left panel + right panel) ──────────────────────
        content_hbox = QHBoxLayout()

        # ── LEFT PANEL ───────────────────────────────────────────────────────
        left_vbox = QVBoxLayout()

        grp_show = QGroupBox("Show labels on:")
        show_layout = QVBoxLayout(grp_show)

        self.lbl_chk_axis     = QCheckBox("Axis line")
        self.lbl_chk_inner    = QCheckBox("Inner circle")
        self.lbl_chk_outer    = QCheckBox("Outer circle")

        self.lbl_chk_axis.setChecked(self.cfg.get(f"{self.current_axis}_lbl_axis", True))
        self.lbl_chk_inner.setChecked(self.cfg.get(f"{self.current_axis}_lbl_inner", False))
        self.lbl_chk_inner.setEnabled(False)   # greyed-out like reference
        self.lbl_chk_outer.setChecked(self.cfg.get(f"{self.current_axis}_lbl_outer", False))

        self.lbl_chk_axis.stateChanged.connect(
            lambda s: self.update_cfg(f"{self.current_axis}_lbl_axis", s == Qt.CheckState.Checked.value))
        self.lbl_chk_outer.stateChanged.connect(
            lambda s: self.update_cfg(f"{self.current_axis}_lbl_outer", s == Qt.CheckState.Checked.value))

        show_layout.addWidget(self.lbl_chk_axis)
        show_layout.addWidget(self.lbl_chk_inner)
        show_layout.addWidget(self.lbl_chk_outer)
        left_vbox.addWidget(grp_show)
        left_vbox.addStretch()

        # Label skip
        skip_hbox = QHBoxLayout()
        skip_hbox.addWidget(QLabel("Label skip:"))
        self.lbl_skip = QSpinBox()
        self.lbl_skip.setRange(1, 100)
        self.lbl_skip.setFixedWidth(70)
        self.lbl_skip.setValue(self.cfg.get(f"{self.current_axis}_lbl_skip", 1))
        self.lbl_skip.valueChanged.connect(
            lambda v: self.update_cfg(f"{self.current_axis}_lbl_skip", v))
        skip_hbox.addWidget(self.lbl_skip)
        skip_hbox.addStretch()
        left_vbox.addLayout(skip_hbox)

        content_hbox.addLayout(left_vbox, 1)

        # ── Vertical divider ─────────────────────────────────────────────────
        vline = QFrame()
        vline.setFrameShape(QFrame.Shape.VLine)
        vline.setFrameShadow(QFrame.Shadow.Sunken)
        content_hbox.addWidget(vline)

        # ── RIGHT PANEL ──────────────────────────────────────────────────────
        right_form = QFormLayout()
        right_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        right_form.setHorizontalSpacing(10)
        right_form.setVerticalSpacing(8)

        # Color
        self._lbl_color = QColor(self.cfg.get(f"{self.current_axis}_lbl_color", "#000000"))
        self.btn_lbl_color = QPushButton()
        self._update_lbl_color_btn()
        self.btn_lbl_color.setFixedWidth(120)
        self.btn_lbl_color.clicked.connect(self._pick_lbl_color)
        right_form.addRow("Color:", self.btn_lbl_color)

        # Font
        font_hbox = QHBoxLayout()
        self.cb_lbl_font = QComboBox()
        self.cb_lbl_font.addItems([
            "Arial", "Times New Roman", "Courier New",
            "Georgia", "Verdana", "Tahoma", "Calibri"
        ])
        self.cb_lbl_font.setCurrentText(self.cfg.get(f"{self.current_axis}_lbl_font", "Arial"))
        self.cb_lbl_font.currentTextChanged.connect(
            lambda t: self.update_cfg(f"{self.current_axis}_lbl_font", t))
        font_hbox.addWidget(self.cb_lbl_font, 1)

        self.sp_lbl_fontsize = QSpinBox()
        self.sp_lbl_fontsize.setRange(1, 72)
        self.sp_lbl_fontsize.setFixedWidth(55)
        self.sp_lbl_fontsize.setValue(self.cfg.get(f"{self.current_axis}_lbl_fontsize", 16))
        self.sp_lbl_fontsize.valueChanged.connect(
            lambda v: self.update_cfg(f"{self.current_axis}_lbl_fontsize", v))
        font_hbox.addWidget(self.sp_lbl_fontsize)

        self.btn_lbl_bold = QPushButton("B")
        self.btn_lbl_bold.setCheckable(True)
        self.btn_lbl_bold.setChecked(self.cfg.get(f"{self.current_axis}_lbl_bold", False))
        self.btn_lbl_bold.setFixedWidth(36)
        self.btn_lbl_bold.setStyleSheet("font-weight: bold; padding: 0px;")
        self.btn_lbl_bold.toggled.connect(
            lambda c: self.update_cfg(f"{self.current_axis}_lbl_bold", c))
        font_hbox.addWidget(self.btn_lbl_bold)

        self.btn_lbl_italic = QPushButton("I")
        self.btn_lbl_italic.setCheckable(True)
        self.btn_lbl_italic.setChecked(self.cfg.get(f"{self.current_axis}_lbl_italic", False))
        self.btn_lbl_italic.setFixedWidth(36)
        self.btn_lbl_italic.setStyleSheet("font-style: italic; padding: 0px;")
        self.btn_lbl_italic.toggled.connect(
            lambda c: self.update_cfg(f"{self.current_axis}_lbl_italic", c))
        font_hbox.addWidget(self.btn_lbl_italic)

        self.btn_lbl_more = QPushButton("...")
        self.btn_lbl_more.setFixedWidth(28)
        font_hbox.addWidget(self.btn_lbl_more)
        right_form.addRow("Font:", font_hbox)

        # Format
        self.cb_lbl_format = QComboBox()
        self.cb_lbl_format.addItems(["Normal", "Scientific"])
        self.cb_lbl_format.setCurrentText(self.cfg.get(f"{self.current_axis}_lbl_format", "Normal"))
        self.cb_lbl_format.setFixedWidth(160)
        self.cb_lbl_format.currentTextChanged.connect(
            lambda t: self.update_cfg(f"{self.current_axis}_lbl_format", t))
        right_form.addRow("Format:", self.cb_lbl_format)

        # Offset from line (%)
        self.le_lbl_offset = QLineEdit(str(self.cfg.get(f"{self.current_axis}_lbl_offset", 1)))
        self.le_lbl_offset.setFixedWidth(120)
        self.le_lbl_offset.editingFinished.connect(self._apply_lbl_offset)
        right_form.addRow("Offset from line (%):", self.le_lbl_offset)

        # Orient labels
        self.cb_lbl_orient = QComboBox()
        self.cb_lbl_orient.addItems(["At angle", "Horizontal", "Vertical", "Along axis"])
        self.cb_lbl_orient.setCurrentText(self.cfg.get(f"{self.current_axis}_lbl_orient", "At angle"))
        self.cb_lbl_orient.setFixedWidth(160)
        self.cb_lbl_orient.currentTextChanged.connect(
            lambda t: self.update_cfg(f"{self.current_axis}_lbl_orient", t))
        right_form.addRow("Orient labels:", self.cb_lbl_orient)

        # Angle (deg)
        self.cb_lbl_angle = QComboBox()
        self.cb_lbl_angle.addItems(["0", "15", "30", "45", "60", "75", "90",
                                    "105", "120", "135", "150", "165", "180",
                                    "-15", "-30", "-45", "-90"])
        self.cb_lbl_angle.setEditable(True)
        self.cb_lbl_angle.setCurrentText(str(self.cfg.get(f"{self.current_axis}_lbl_angle", 0)))
        self.cb_lbl_angle.setFixedWidth(160)
        self.cb_lbl_angle.currentTextChanged.connect(
            lambda t: self.update_cfg(f"{self.current_axis}_lbl_angle", t))
        right_form.addRow("Angle (deg):", self.cb_lbl_angle)

        # Checkboxes row (no label)
        self.chk_lbl_at_intersection = QCheckBox("Show label at axis intersection")
        self.chk_lbl_at_intersection.setChecked(
            self.cfg.get(f"{self.current_axis}_lbl_at_intersection", False))
        self.chk_lbl_at_intersection.stateChanged.connect(
            lambda s: self.update_cfg(f"{self.current_axis}_lbl_at_intersection",
                                      s == Qt.CheckState.Checked.value))
        right_form.addRow("", self.chk_lbl_at_intersection)

        self.chk_lbl_erase_behind = QCheckBox("Erase behind labels")
        self.chk_lbl_erase_behind.setChecked(
            self.cfg.get(f"{self.current_axis}_lbl_erase_behind", True))
        self.chk_lbl_erase_behind.stateChanged.connect(
            lambda s: self.update_cfg(f"{self.current_axis}_lbl_erase_behind",
                                      s == Qt.CheckState.Checked.value))
        right_form.addRow("", self.chk_lbl_erase_behind)

        right_widget = QWidget()
        right_widget.setLayout(right_form)
        content_hbox.addWidget(right_widget, 2)

        outer.addLayout(content_hbox, 1)

        # ── Bottom: Tick Mark and Label Spacing ───────────────────────────────
        grp_lbl_spacing = QGroupBox("Tick Mark and Label Spacing")
        spacing_hbox = QHBoxLayout(grp_lbl_spacing)

        self.chk_lbl_auto_spacing = QCheckBox("Auto Spacing")
        self.chk_lbl_auto_spacing.setChecked(
            self.cfg.get(f"{self.current_axis}_lbl_auto_spacing", True))
        self.chk_lbl_auto_spacing.stateChanged.connect(
            lambda s: self._on_lbl_auto_spacing(s == Qt.CheckState.Checked.value))
        spacing_hbox.addWidget(self.chk_lbl_auto_spacing)

        spacing_hbox.addSpacing(16)
        spacing_hbox.addWidget(QLabel("Spacing:"))
        self.le_lbl_spacing = QLineEdit(str(self.cfg.get(f"{self.current_axis}_lbl_spacing", 30)))
        self.le_lbl_spacing.setFixedWidth(70)
        self.le_lbl_spacing.setEnabled(not self.chk_lbl_auto_spacing.isChecked())
        self.le_lbl_spacing.editingFinished.connect(self._apply_lbl_spacing)
        spacing_hbox.addWidget(self.le_lbl_spacing)

        spacing_hbox.addSpacing(30)
        spacing_hbox.addWidget(QLabel("Anchor:"))
        self.le_lbl_anchor = QLineEdit(str(self.cfg.get(f"{self.current_axis}_lbl_anchor", 0)))
        self.le_lbl_anchor.setFixedWidth(70)
        self.le_lbl_anchor.editingFinished.connect(self._apply_lbl_anchor)
        spacing_hbox.addWidget(self.le_lbl_anchor)
        spacing_hbox.addStretch()

        outer.addWidget(grp_lbl_spacing)

    def setup_title_tab(self):
        outer = QVBoxLayout(self.tab_title)

        # ── Main content area (left panel + right panel) ──────────────────────
        content_hbox = QHBoxLayout()

        # ── LEFT PANEL ───────────────────────────────────────────────────────
        left_vbox = QVBoxLayout()
        lbl_show = QLabel("Show Title On:")
        left_vbox.addWidget(lbl_show)

        chk_layout = QVBoxLayout()
        chk_layout.setContentsMargins(15, 0, 0, 0)

        self.title_chk_axis     = QCheckBox("Axis line")
        self.title_chk_inner    = QCheckBox("Inner circle")
        self.title_chk_outer    = QCheckBox("Outer circle")

        self.title_chk_axis.setChecked(self.cfg.get(f"{self.current_axis}_title_axis", True))
        self.title_chk_inner.setChecked(self.cfg.get(f"{self.current_axis}_title_inner", False))
        self.title_chk_inner.setEnabled(False) # greyed-out like reference
        self.title_chk_outer.setChecked(self.cfg.get(f"{self.current_axis}_title_outer", False))

        self.title_chk_axis.stateChanged.connect(lambda s: self.update_cfg(f"{self.current_axis}_title_axis", s == Qt.CheckState.Checked.value))
        self.title_chk_outer.stateChanged.connect(lambda s: self.update_cfg(f"{self.current_axis}_title_outer", s == Qt.CheckState.Checked.value))

        chk_layout.addWidget(self.title_chk_axis)
        chk_layout.addWidget(self.title_chk_inner)
        chk_layout.addWidget(self.title_chk_outer)
        
        left_vbox.addLayout(chk_layout)
        left_vbox.addStretch()
        content_hbox.addLayout(left_vbox, 1)

        # ── RIGHT PANEL ──────────────────────────────────────────────────────
        right_vbox = QVBoxLayout()
        right_form = QFormLayout()
        right_form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        right_form.setHorizontalSpacing(15)
        right_form.setVerticalSpacing(8)

        # Color
        self._title_color = QColor(self.cfg.get(f"{self.current_axis}_title_color", "#000000"))
        self.btn_title_color = QPushButton()
        self._update_title_color_btn()
        self.btn_title_color.setFixedWidth(120)
        self.btn_title_color.clicked.connect(self._pick_title_color)
        right_form.addRow("Color:", self.btn_title_color)

        # Font
        font_hbox = QHBoxLayout()
        font_hbox.setSpacing(5)
        self.cb_title_font = QComboBox()
        self.cb_title_font.addItems([
            "Arial", "Times New Roman", "Courier New",
            "Georgia", "Verdana", "Tahoma", "Calibri"
        ])
        self.cb_title_font.setCurrentText(self.cfg.get(f"{self.current_axis}_title_font", "Arial"))
        self.cb_title_font.currentTextChanged.connect(lambda t: self.update_cfg(f"{self.current_axis}_title_font", t))
        font_hbox.addWidget(self.cb_title_font, 1)

        self.sp_title_fontsize = QDoubleSpinBox()
        self.sp_title_fontsize.setRange(1.0, 72.0)
        self.sp_title_fontsize.setSingleStep(0.1)
        self.sp_title_fontsize.setFixedWidth(55)
        self.sp_title_fontsize.setValue(self.cfg.get(f"{self.current_axis}_title_fontsize", 3.6))
        self.sp_title_fontsize.valueChanged.connect(lambda v: self.update_cfg(f"{self.current_axis}_title_fontsize", v))
        font_hbox.addWidget(self.sp_title_fontsize)

        self.btn_title_bold = QPushButton("B")
        self.btn_title_bold.setCheckable(True)
        self.btn_title_bold.setChecked(self.cfg.get(f"{self.current_axis}_title_bold", False))
        self.btn_title_bold.setFixedWidth(36)
        self.btn_title_bold.setStyleSheet("font-weight: bold; padding: 0px;")
        self.btn_title_bold.toggled.connect(lambda c: self.update_cfg(f"{self.current_axis}_title_bold", c))
        font_hbox.addWidget(self.btn_title_bold)

        self.btn_title_italic = QPushButton("I")
        self.btn_title_italic.setCheckable(True)
        self.btn_title_italic.setChecked(self.cfg.get(f"{self.current_axis}_title_italic", False))
        self.btn_title_italic.setFixedWidth(36)
        self.btn_title_italic.setStyleSheet("font-style: italic; padding: 0px;")
        self.btn_title_italic.toggled.connect(lambda c: self.update_cfg(f"{self.current_axis}_title_italic", c))
        font_hbox.addWidget(self.btn_title_italic)

        self.btn_title_more = QPushButton("...")
        self.btn_title_more.setFixedWidth(28)
        font_hbox.addWidget(self.btn_title_more)
        right_form.addRow("Font:", font_hbox)

        # Offset from line (%)
        default_offset = 10 if "Y" in self.current_axis else 6
        self.le_title_offset = QLineEdit(str(self.cfg.get(f"{self.current_axis}_title_offset", default_offset)))
        self.le_title_offset.editingFinished.connect(self._apply_title_offset)
        right_form.addRow("Offset from line (%):", self.le_title_offset)

        # Position along line (%)
        self.le_title_pos = QLineEdit(str(self.cfg.get(f"{self.current_axis}_title_pos", 3)))
        self.le_title_pos.editingFinished.connect(self._apply_title_pos)
        right_form.addRow("Position along line (%):", self.le_title_pos)

        right_widget = QWidget()
        right_widget.setLayout(right_form)
        right_vbox.addWidget(right_widget)
        right_vbox.addStretch()
        
        content_hbox.addLayout(right_vbox, 2)
        outer.addLayout(content_hbox)
        
        outer.addStretch()
        
        # ── Bottom: Text Input ───────────────────────────────────────────────
        self.bg_title_mode = QButtonGroup(self)
        self.rb_title_var = QRadioButton("Use variable name")
        self.rb_title_text = QRadioButton("Use text:")
        
        self.bg_title_mode.addButton(self.rb_title_var, 0)
        self.bg_title_mode.addButton(self.rb_title_text, 1)
        
        mode = self.cfg.get(f"{self.current_axis}_title_mode", "Use variable name")
        if mode == "Use text:": self.rb_title_text.setChecked(True)
        else: self.rb_title_var.setChecked(True)
            
        self.bg_title_mode.buttonClicked.connect(lambda b: self.update_cfg(f"{self.current_axis}_title_mode", b.text()))
        
        outer.addWidget(self.rb_title_var)
        outer.addWidget(self.rb_title_text)
        
        self.le_title_text = QLineEdit(self.cfg.get(f"{self.current_axis}_title_text", ""))
        self.le_title_text.setEnabled(self.rb_title_text.isChecked())
        self.le_title_text.editingFinished.connect(self._apply_title_text)
        
        # Wire toggle dependency
        self.rb_title_text.toggled.connect(self.le_title_text.setEnabled)
        
        outer.addWidget(self.le_title_text)
        
        lbl_hint = QLabel("💡 <i>Hint: Use <b>$...$</b> for LaTeX symbols (e.g. <b>$\\alpha$</b>), superscripts (e.g. <b>$x^2$</b>), or subscripts (e.g. <b>$x_1$</b>).</i>")
        lbl_hint.setStyleSheet("color: #64748b; font-size: 11px;")
        outer.addWidget(lbl_hint)

    def setup_line_tab(self):
        layout = QVBoxLayout(self.tab_line)
        
        self.chk_line_show_axis = QCheckBox("Show Axis line")
        self.chk_line_show_axis.setChecked(self.cfg.get(f"{self.current_axis}_line_show_axis", True))
        self.chk_line_show_axis.stateChanged.connect(
            lambda s: self.update_cfg(f"{self.current_axis}_line_show_axis", s == Qt.CheckState.Checked.value))
        layout.addWidget(self.chk_line_show_axis)
        
        self.chk_line_show_grid_border = QCheckBox("Show grid border")
        self.chk_line_show_grid_border.setChecked(self.cfg.get(f"{self.current_axis}_line_show_grid_border", False))
        self.chk_line_show_grid_border.stateChanged.connect(
            lambda s: self.update_cfg(f"{self.current_axis}_line_show_grid_border", s == Qt.CheckState.Checked.value))
        layout.addWidget(self.chk_line_show_grid_border)
        
        layout.addStretch()

    # ── Title tab helpers ─────────────────────────────────────────────────────
    def _update_title_color_btn(self):
        c = self._title_color
        pixmap = QPixmap(14, 14)
        pixmap.fill(c)
        self.btn_title_color.setIcon(QIcon(pixmap))
        
        color_hex = c.name().lower()
        color_map = {
            "#000000": "Black", "#ffffff": "White", "#ff0000": "Red", 
            "#00ff00": "Green", "#0000ff": "Blue", "#ffff00": "Yellow", 
            "#00ffff": "Cyan", "#ff00ff": "Magenta"
        }
        self.btn_title_color.setText(color_map.get(color_hex, color_hex.upper()))
        self.btn_title_color.setStyleSheet("")

    def _pick_title_color(self):
        c = QColorDialog.getColor(self._title_color, self, "Title Color")
        if c.isValid():
            self._title_color = c
            self._update_title_color_btn()
            self.update_cfg(f"{self.current_axis}_title_color", c.name())

    def _apply_title_offset(self):
        try:
            v = float(self.le_title_offset.text())
            self.update_cfg(f"{self.current_axis}_title_offset", v)
        except ValueError:
            pass
            
    def _apply_title_pos(self):
        try:
            v = float(self.le_title_pos.text())
            self.update_cfg(f"{self.current_axis}_title_pos", v)
        except ValueError:
            pass
            
    def _apply_title_text(self):
        self.update_cfg(f"{self.current_axis}_title_text", self.le_title_text.text())

    # ── Labels tab helpers ────────────────────────────────────────────────────
    def _update_lbl_color_btn(self):
        c = self._lbl_color
        pixmap = QPixmap(14, 14)
        pixmap.fill(c)
        self.btn_lbl_color.setIcon(QIcon(pixmap))
        
        color_hex = c.name().lower()
        color_map = {
            "#000000": "Black", "#ffffff": "White", "#ff0000": "Red", 
            "#00ff00": "Green", "#0000ff": "Blue", "#ffff00": "Yellow", 
            "#00ffff": "Cyan", "#ff00ff": "Magenta"
        }
        self.btn_lbl_color.setText(color_map.get(color_hex, color_hex.upper()))
        self.btn_lbl_color.setStyleSheet("")

    def _pick_lbl_color(self):
        c = QColorDialog.getColor(self._lbl_color, self, "Label Color")
        if c.isValid():
            self._lbl_color = c
            self._update_lbl_color_btn()
            self.update_cfg(f"{self.current_axis}_lbl_color", c.name())

    def _apply_lbl_offset(self):
        try:
            v = float(self.le_lbl_offset.text())
            self.update_cfg(f"{self.current_axis}_lbl_offset", v)
        except ValueError:
            pass

    def _apply_lbl_spacing(self):
        try:
            v = float(self.le_lbl_spacing.text())
            self.update_cfg(f"{self.current_axis}_lbl_spacing", v)
        except ValueError:
            pass

    def _apply_lbl_anchor(self):
        try:
            v = float(self.le_lbl_anchor.text())
            self.update_cfg(f"{self.current_axis}_lbl_anchor", v)
        except ValueError:
            pass

    def _on_lbl_auto_spacing(self, checked: bool):
        self.le_lbl_spacing.setEnabled(not checked)
        self.update_cfg(f"{self.current_axis}_lbl_auto_spacing", checked)

    def _apply_grid_value(self, key_suffix, val_str):
        try:
            v = float(val_str)
            self.update_cfg(f"{self.current_axis}_{key_suffix}", v)
        except ValueError:
            pass

    def reset_range(self):
        # Clear the UI inputs and internal dict for this axis
        self.le_min.blockSignals(True)
        self.le_max.blockSignals(True)
        self.le_min.setText("")
        self.le_max.setText("")
        self.le_min.blockSignals(False)
        self.le_max.blockSignals(False)
        
        self.cfg[f"{self.current_axis}_min"] = None
        self.cfg[f"{self.current_axis}_max"] = None
        
        # Apply to main window, recompute limits, and get them
        self.apply_changes()
        
        if "X" in self.current_axis:
            lims = self.parent_window.ax.get_xlim()
        else:
            lims = self.parent_window.ax.get_ylim()
            
        self.le_min.blockSignals(True)
        self.le_max.blockSignals(True)
        self.le_min.setText(str(round(lims[0], 4)))
        self.le_max.setText(str(round(lims[1], 4)))
        self.le_min.blockSignals(False)
        self.le_max.blockSignals(False)

    def _on_nice_fit_changed(self, state):
        is_checked = (state == Qt.CheckState.Checked.value)
        self.update_cfg("nice_fit", is_checked)
        if is_checked:
            self.reset_range()

    def on_axis_changed(self, btn):
        self.update_min_max("min", self.le_min.text())
        self.update_min_max("max", self.le_max.text())
        self.current_axis = btn.text()
        self.chk_show_axis.setText(f"Show {self.current_axis}-Axis")
        # Load state into form
        self.chk_show_axis.blockSignals(True)
        self.chk_show_axis.setChecked(self.cfg.get(f"{self.current_axis}_show", True))
        self.chk_show_axis.blockSignals(False)
        
        self.chk_preserve.blockSignals(True)
        self.chk_preserve.setChecked(self.cfg.get(f"{self.current_axis}_preserve", True))
        self.chk_preserve.blockSignals(False)
        
        self.chk_log.blockSignals(True)
        self.chk_log.setChecked(self.cfg.get(f"{self.current_axis}_log", False))
        self.chk_log.blockSignals(False)
        
        self.chk_reverse.blockSignals(True)
        self.chk_reverse.setChecked(self.cfg.get(f"{self.current_axis}_reverse", False))
        self.chk_reverse.blockSignals(False)
        
        # Load Ticks Tab state
        self.chk_show_ticks.blockSignals(True)
        self.chk_show_ticks.setChecked(self.cfg.get(f"{self.current_axis}_show_ticks", True))
        self.chk_show_ticks.blockSignals(False)
        
        self.cb_tick_dir.blockSignals(True)
        self.cb_tick_dir.setCurrentText(self.cfg.get(f"{self.current_axis}_tick_dir", "Out").capitalize())
        self.cb_tick_dir.blockSignals(False)
        
        self.sp_tick_len.blockSignals(True)
        self.sp_tick_len.setValue(self.cfg.get(f"{self.current_axis}_tick_len", 4.0))
        self.sp_tick_len.blockSignals(False)
        
        self.sp_tick_width.blockSignals(True)
        self.sp_tick_width.setValue(self.cfg.get(f"{self.current_axis}_tick_width", 1.0))
        self.sp_tick_width.blockSignals(False)
        
        self.chk_show_minor_ticks.blockSignals(True)
        self.chk_show_minor_ticks.setChecked(self.cfg.get(f"{self.current_axis}_show_minor_ticks", False))
        self.chk_show_minor_ticks.blockSignals(False)
        
        self.sp_minor_tick_len.blockSignals(True)
        self.sp_minor_tick_len.setValue(self.cfg.get(f"{self.current_axis}_minor_tick_len", 2.0))
        self.sp_minor_tick_len.blockSignals(False)
        
        # Load Spacing state
        self.chk_auto_spacing.blockSignals(True)
        self.chk_auto_spacing.setChecked(self.cfg.get(f"{self.current_axis}_auto_spacing", True))
        self.chk_auto_spacing.blockSignals(False)
        
        self.sp_spacing.blockSignals(True)
        self.sp_spacing.setValue(self.cfg.get(f"{self.current_axis}_spacing", 30.0))
        self.sp_spacing.blockSignals(False)
        
        self.sp_spacing.setEnabled(not self.chk_auto_spacing.isChecked())

        # ── Reload Grid tab ───────────────────────────────────────────────────
        self.chk_grid_show.blockSignals(True)
        self.chk_grid_show.setChecked(self.cfg.get(f"{self.current_axis}_grid_show", True))
        self.chk_grid_show.blockSignals(False)

        self.cb_grid_pattern.blockSignals(True)
        self.cb_grid_pattern.setCurrentText(self.cfg.get(f"{self.current_axis}_grid_pattern", "Solid"))
        self.cb_grid_pattern.blockSignals(False)

        self.le_grid_len.blockSignals(True)
        self.le_grid_len.setText(str(self.cfg.get(f"{self.current_axis}_grid_len", 2)))
        self.le_grid_len.blockSignals(False)

        self.cb_grid_thick.blockSignals(True)
        self.cb_grid_thick.setCurrentText(str(self.cfg.get(f"{self.current_axis}_grid_thick", 0.1)))
        self.cb_grid_thick.blockSignals(False)

        self._grid_color = QColor(self.cfg.get(f"{self.current_axis}_grid_color", "#000000"))
        self._update_color_btn(self.btn_grid_color, self._grid_color)

        self.cb_grid_order.blockSignals(True)
        self.cb_grid_order.setCurrentText(self.cfg.get(f"{self.current_axis}_grid_order", "First"))
        self.cb_grid_order.blockSignals(False)

        self.chk_minor_grid_show.blockSignals(True)
        self.chk_minor_grid_show.setChecked(self.cfg.get(f"{self.current_axis}_minor_grid_show", False))
        self.chk_minor_grid_show.blockSignals(False)

        self.cb_minor_grid_pattern.blockSignals(True)
        self.cb_minor_grid_pattern.setCurrentText(self.cfg.get(f"{self.current_axis}_minor_grid_pattern", "Dotted"))
        self.cb_minor_grid_pattern.blockSignals(False)

        self.le_minor_grid_len.blockSignals(True)
        self.le_minor_grid_len.setText(str(self.cfg.get(f"{self.current_axis}_minor_grid_len", 2)))
        self.le_minor_grid_len.blockSignals(False)

        self.cb_minor_grid_thick.blockSignals(True)
        self.cb_minor_grid_thick.setCurrentText(str(self.cfg.get(f"{self.current_axis}_minor_grid_thick", 0.1)))
        self.cb_minor_grid_thick.blockSignals(False)

        self._minor_grid_color = QColor(self.cfg.get(f"{self.current_axis}_minor_grid_color", "#000000"))
        self._update_color_btn(self.btn_minor_grid_color, self._minor_grid_color)

        self.cb_minor_grid_order.blockSignals(True)
        self.cb_minor_grid_order.setCurrentText(self.cfg.get(f"{self.current_axis}_minor_grid_order", "First"))
        self.cb_minor_grid_order.blockSignals(False)

        # Update enabled state for minor grid widgets
        minor_enabled = self.chk_minor_grid_show.isChecked()
        self.cb_minor_grid_pattern.setEnabled(minor_enabled)
        self.le_minor_grid_len.setEnabled(minor_enabled)
        self.cb_minor_grid_thick.setEnabled(minor_enabled)
        self.btn_minor_grid_color.setEnabled(minor_enabled)
        self.cb_minor_grid_order.setEnabled(minor_enabled)

        self.chk_dot_grid.blockSignals(True)
        self.chk_dot_grid.setChecked(self.cfg.get(f"{self.current_axis}_dot_grid", False))
        self.chk_dot_grid.blockSignals(False)

        self.le_dot_size.blockSignals(True)
        self.le_dot_size.setText(str(self.cfg.get(f"{self.current_axis}_dot_size", 0.0045)))
        self.le_dot_size.blockSignals(False)

        self._dot_color = QColor(self.cfg.get(f"{self.current_axis}_dot_color", "#000000"))
        self._update_color_btn(self.btn_dot_color, self._dot_color)

        self.le_dot_size.setEnabled(self.chk_dot_grid.isChecked())
        self.btn_dot_color.setEnabled(self.chk_dot_grid.isChecked())

        # ── Reload Title tab ──────────────────────────────────────────────────
        self.title_chk_axis.blockSignals(True)
        self.title_chk_axis.setChecked(self.cfg.get(f"{self.current_axis}_title_axis", True))
        self.title_chk_axis.blockSignals(False)

        self.title_chk_inner.blockSignals(True)
        self.title_chk_inner.setChecked(self.cfg.get(f"{self.current_axis}_title_inner", False))
        self.title_chk_inner.blockSignals(False)

        self.title_chk_outer.blockSignals(True)
        self.title_chk_outer.setChecked(self.cfg.get(f"{self.current_axis}_title_outer", False))
        self.title_chk_outer.blockSignals(False)

        new_title_color = QColor(self.cfg.get(f"{self.current_axis}_title_color", "#000000"))
        self._title_color = new_title_color
        self._update_title_color_btn()

        self.cb_title_font.blockSignals(True)
        self.cb_title_font.setCurrentText(self.cfg.get(f"{self.current_axis}_title_font", "Arial"))
        self.cb_title_font.blockSignals(False)

        self.sp_title_fontsize.blockSignals(True)
        self.sp_title_fontsize.setValue(self.cfg.get(f"{self.current_axis}_title_fontsize", 3.6))
        self.sp_title_fontsize.blockSignals(False)

        self.btn_title_bold.blockSignals(True)
        self.btn_title_bold.setChecked(self.cfg.get(f"{self.current_axis}_title_bold", False))
        self.btn_title_bold.blockSignals(False)

        self.btn_title_italic.blockSignals(True)
        self.btn_title_italic.setChecked(self.cfg.get(f"{self.current_axis}_title_italic", False))
        self.btn_title_italic.blockSignals(False)

        default_offset = 10 if "Y" in self.current_axis else 6
        self.le_title_offset.blockSignals(True)
        self.le_title_offset.setText(str(self.cfg.get(f"{self.current_axis}_title_offset", default_offset)))
        self.le_title_offset.blockSignals(False)

        self.le_title_pos.blockSignals(True)
        self.le_title_pos.setText(str(self.cfg.get(f"{self.current_axis}_title_pos", 3)))
        self.le_title_pos.blockSignals(False)

        # Bottom modes
        self.rb_title_text.blockSignals(True)
        self.rb_title_var.blockSignals(True)
        mode = self.cfg.get(f"{self.current_axis}_title_mode", "Use variable name")
        if mode == "Use text:": self.rb_title_text.setChecked(True)
        else: self.rb_title_var.setChecked(True)
        self.rb_title_text.blockSignals(False)
        self.rb_title_var.blockSignals(False)

        self.le_title_text.blockSignals(True)
        self.le_title_text.setText(self.cfg.get(f"{self.current_axis}_title_text", ""))
        self.le_title_text.setEnabled(self.rb_title_text.isChecked())
        self.le_title_text.blockSignals(False)

        # ── Reload Labels tab ─────────────────────────────────────────────────
        self.lbl_chk_axis.blockSignals(True)
        self.lbl_chk_axis.setChecked(self.cfg.get(f"{self.current_axis}_lbl_axis", True))
        self.lbl_chk_axis.blockSignals(False)

        self.lbl_chk_inner.blockSignals(True)
        self.lbl_chk_inner.setChecked(self.cfg.get(f"{self.current_axis}_lbl_inner", False))
        self.lbl_chk_inner.blockSignals(False)

        self.lbl_chk_outer.blockSignals(True)
        self.lbl_chk_outer.setChecked(self.cfg.get(f"{self.current_axis}_lbl_outer", False))
        self.lbl_chk_outer.blockSignals(False)

        self.lbl_skip.blockSignals(True)
        self.lbl_skip.setValue(self.cfg.get(f"{self.current_axis}_lbl_skip", 1))
        self.lbl_skip.blockSignals(False)

        new_color = QColor(self.cfg.get(f"{self.current_axis}_lbl_color", "#000000"))
        self._lbl_color = new_color
        self._update_lbl_color_btn()

        self.cb_lbl_font.blockSignals(True)
        self.cb_lbl_font.setCurrentText(self.cfg.get(f"{self.current_axis}_lbl_font", "Arial"))
        self.cb_lbl_font.blockSignals(False)

        self.sp_lbl_fontsize.blockSignals(True)
        self.sp_lbl_fontsize.setValue(self.cfg.get(f"{self.current_axis}_lbl_fontsize", 8))
        self.sp_lbl_fontsize.blockSignals(False)

        self.btn_lbl_bold.blockSignals(True)
        self.btn_lbl_bold.setChecked(self.cfg.get(f"{self.current_axis}_lbl_bold", False))
        self.btn_lbl_bold.blockSignals(False)

        self.btn_lbl_italic.blockSignals(True)
        self.btn_lbl_italic.setChecked(self.cfg.get(f"{self.current_axis}_lbl_italic", False))
        self.btn_lbl_italic.blockSignals(False)

        self.cb_lbl_format.blockSignals(True)
        self.cb_lbl_format.setCurrentText(self.cfg.get(f"{self.current_axis}_lbl_format", "Normal"))
        self.cb_lbl_format.blockSignals(False)

        self.le_lbl_offset.blockSignals(True)
        self.le_lbl_offset.setText(str(self.cfg.get(f"{self.current_axis}_lbl_offset", 1)))
        self.le_lbl_offset.blockSignals(False)

        self.cb_lbl_orient.blockSignals(True)
        self.cb_lbl_orient.setCurrentText(self.cfg.get(f"{self.current_axis}_lbl_orient", "At angle"))
        self.cb_lbl_orient.blockSignals(False)

        self.cb_lbl_angle.blockSignals(True)
        self.cb_lbl_angle.setCurrentText(str(self.cfg.get(f"{self.current_axis}_lbl_angle", 0)))
        self.cb_lbl_angle.blockSignals(False)

        self.chk_lbl_at_intersection.blockSignals(True)
        self.chk_lbl_at_intersection.setChecked(
            self.cfg.get(f"{self.current_axis}_lbl_at_intersection", False))
        self.chk_lbl_at_intersection.blockSignals(False)

        self.chk_lbl_erase_behind.blockSignals(True)
        self.chk_lbl_erase_behind.setChecked(
            self.cfg.get(f"{self.current_axis}_lbl_erase_behind", True))
        self.chk_lbl_erase_behind.blockSignals(False)

        self.chk_lbl_auto_spacing.blockSignals(True)
        auto = self.cfg.get(f"{self.current_axis}_lbl_auto_spacing", True)
        self.chk_lbl_auto_spacing.setChecked(auto)
        self.chk_lbl_auto_spacing.blockSignals(False)
        self.le_lbl_spacing.setEnabled(not auto)

        self.le_lbl_spacing.blockSignals(True)
        self.le_lbl_spacing.setText(str(self.cfg.get(f"{self.current_axis}_lbl_spacing", 30)))
        self.le_lbl_spacing.blockSignals(False)

        self.le_lbl_anchor.blockSignals(True)
        self.le_lbl_anchor.setText(str(self.cfg.get(f"{self.current_axis}_lbl_anchor", 0)))
        self.le_lbl_anchor.blockSignals(False)

        # ── Reload Line tab ───────────────────────────────────────────────────
        if hasattr(self, 'chk_line_show_axis'):
            self.chk_line_show_axis.blockSignals(True)
            self.chk_line_show_axis.setChecked(self.cfg.get(f"{self.current_axis}_line_show_axis", True))
            self.chk_line_show_axis.blockSignals(False)
            
            self.chk_line_show_grid_border.blockSignals(True)
            self.chk_line_show_grid_border.setChecked(self.cfg.get(f"{self.current_axis}_line_show_grid_border", False))
            self.chk_line_show_grid_border.blockSignals(False)

        lims = self.parent_window.ax.get_xlim() if "X" in self.current_axis else self.parent_window.ax.get_ylim()
        self.le_min.blockSignals(True)
        self.le_max.blockSignals(True)
        
        custom_min = self.cfg.get(f"{self.current_axis}_min", None)
        custom_max = self.cfg.get(f"{self.current_axis}_max", None)
        
        self.le_min.setText(str(round(custom_min if custom_min is not None else lims[0], 4)))
        self.le_max.setText(str(round(custom_max if custom_max is not None else lims[1], 4)))
        
        self.le_min.blockSignals(False)
        self.le_max.blockSignals(False)

    def _update_color_btn(self, btn: QPushButton, color: QColor):
        pixmap = QPixmap(14, 14)
        pixmap.fill(color)
        btn.setIcon(QIcon(pixmap))
        color_hex = color.name().lower()
        color_map = {
            "#000000": "Black", "#ffffff": "White", "#ff0000": "Red", 
            "#00ff00": "Green", "#0000ff": "Blue", "#ffff00": "Yellow", 
            "#00ffff": "Cyan", "#ff00ff": "Magenta"
        }
        btn.setText(color_map.get(color_hex, color_hex.upper()))
        
    def _pick_color(self, internal_attr_name: str, btn: QPushButton, cfg_key: str):
        current_color = getattr(self, internal_attr_name)
        c = QColorDialog.getColor(current_color, self, "Select Color")
        if c.isValid():
            setattr(self, internal_attr_name, c)
            self._update_color_btn(btn, c)
            self.update_cfg(cfg_key, c.name())

    def update_min_max(self, bound, val_str):
        v = val_str.strip().lower()
        if not v or v == "auto" or v == "none":
            self.cfg[f"{self.current_axis}_{bound}"] = None
        else:
            try:
                self.cfg[f"{self.current_axis}_{bound}"] = float(val_str)
            except ValueError:
                pass
            
    def update_cfg(self, key, value):
        self.cfg[key] = value
        
        # Keep main window cfg in sync to prevent apply button requiring a double-click
        self.parent_window.axis_cfg[key] = value
        
