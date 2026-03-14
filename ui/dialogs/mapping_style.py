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


class MappingStyleDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Mapping Style")
        self.resize(950, 450)
        self.parent_window = parent
        
        self.maps = copy.deepcopy(parent.maps)
        self.var_names = parent.var_names
        
        layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabBar::tab { padding: 8px 15px; border: 1px solid #dcdcdc; border-bottom: none; background: #f0f0f0; color: #333; }
            QTabBar::tab:selected { background: white; font-weight: bold; border-top: 2px solid #1f77b4; }
            QTabWidget::pane { border: 1px solid #dcdcdc; }
        """)
        layout.addWidget(self.tabs)
        
        # -- Definitions Tab --
        self.tab_def = QWidget()
        def_layout = QVBoxLayout(self.tab_def)
        self.table_def = QTableWidget()
        def_layout.addWidget(self.table_def)
        self.tabs.addTab(self.tab_def, "Definitions")
        
        # -- Lines Tab --
        self.tab_lines = QWidget()
        lines_layout = QVBoxLayout(self.tab_lines)
        self.table_lines = QTableWidget()
        lines_layout.addWidget(self.table_lines)
        self.tabs.addTab(self.tab_lines, "Lines")
        
        # -- Curves Tab --
        self.tab_curves = QWidget()
        curves_layout = QVBoxLayout(self.tab_curves)
        self.table_curves = QTableWidget()
        curves_layout.addWidget(self.table_curves)
        self.tabs.addTab(self.tab_curves, "Curves")
        
        # -- Symbols Tab --
        self.tab_symbols = QWidget()
        symbols_layout = QVBoxLayout(self.tab_symbols)
        self.table_symbols = QTableWidget()
        symbols_layout.addWidget(self.table_symbols)
        self.tabs.addTab(self.tab_symbols, "Symbols")
        
        # -- Error Bars Tab --
        self.tab_errorbars = QWidget()
        errorbars_layout = QVBoxLayout(self.tab_errorbars)
        self.table_errorbars = QTableWidget()
        errorbars_layout.addWidget(self.table_errorbars)
        self.tabs.addTab(self.tab_errorbars, "Error Bars")
        
        # Hook up a tab change listener to refresh data
        self.tabs.currentChanged.connect(self.setup_tables)
        
        self.setup_tables()
        
        # Connect item edit signals
        self.table_def.itemChanged.connect(lambda item: self._on_item_changed(self.table_def, item))
        self.table_lines.itemChanged.connect(lambda item: self._on_item_changed(self.table_lines, item))
        self.table_curves.itemChanged.connect(lambda item: self._on_item_changed(self.table_curves, item))
        self.table_symbols.itemChanged.connect(lambda item: self._on_item_changed(self.table_symbols, item))
        self.table_errorbars.itemChanged.connect(lambda item: self._on_item_changed(self.table_errorbars, item))
        
        # Bottom Actions
        btn_layout = QHBoxLayout()
        # Fake "Selection criteria" to match UI
        btn_layout.addWidget(QLabel("Selection criteria:"))
        btn_layout.addWidget(QPushButton("Select"))
        btn_layout.addWidget(QPushButton("Clear"))
        btn_layout.addSpacing(20)
        
        btn_create = QPushButton("Create Map...")
        btn_create.clicked.connect(self.create_map)
        btn_layout.addWidget(btn_create)
        
        btn_copy = QPushButton("Copy Map")
        btn_layout.addWidget(btn_copy)
        
        btn_delete = QPushButton("Delete Map")
        btn_delete.clicked.connect(self.delete_map)
        btn_layout.addWidget(btn_delete)
        
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
        
    def apply_changes(self):
        self.parent_window.maps = copy.deepcopy(self.maps)
        self.parent_window.update_plot()
        
    def accept_changes(self):
        self.apply_changes()
        self.close()
        
    def _on_item_changed(self, table, item):
        row = item.row()
        col = item.column()
        # Map Name is always column 1 in all our tabs
        if col == 1 and row < len(self.maps):
            self.maps[row]["name"] = item.text()
        
    def setup_tables(self, _=None):
        idx = self.tabs.currentIndex()
        if idx == 0:
            self.setup_def_table()
        elif idx == 1:
            self.setup_lines_table()
        elif idx == 2:
            self.setup_curves_table()
        elif idx == 3:
            self.setup_symbols_table()
        elif idx == 4:
            self.setup_errorbars_table()
            
    def setup_def_table(self):
        self.table_def.blockSignals(True)
        self.table_def.clear()
        self.table_def.setColumnCount(5)
        self.table_def.setHorizontalHeaderLabels([
            "Map\nNumber", "Map\nName", "Show\nMap", "X-Axis\nVariable", "Y-Axis\nVariable"
        ])
        
        self.table_def.setRowCount(len(self.maps))
        self.table_def.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table_def.horizontalHeader().setStretchLastSection(True)
        self.table_def.verticalHeader().setVisible(False)
        
        for i, m in enumerate(self.maps):
            item_num = QTableWidgetItem(str(i+1))
            item_num.setFlags(item_num.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table_def.setItem(i, 0, item_num)
            
            item_name = QTableWidgetItem(m.get("name", f"Map {i+1}"))
            self.table_def.setItem(i, 1, item_name)
            
            chk = QCheckBox()
            chk.setChecked(m.get("show", True))
            chk.stateChanged.connect(lambda state, row=i: self.update_map(row, "show", state == Qt.CheckState.Checked.value))
            w = QWidget()
            l = QHBoxLayout(w)
            l.addWidget(chk)
            l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l.setContentsMargins(0,0,0,0)
            self.table_def.setCellWidget(i, 2, w)
            
            combo_x = QComboBox()
            for j, v in enumerate(self.var_names):
                combo_x.addItem(f"{j+1}: {v}", j)
            if m.get("x_var_idx", 0) < len(self.var_names):
                combo_x.setCurrentIndex(m.get("x_var_idx", 0))
            combo_x.currentIndexChanged.connect(lambda idx, row=i: self.update_map(row, "x_var_idx", idx))
            self.table_def.setCellWidget(i, 3, combo_x)
            
            combo_y = QComboBox()
            for j, v in enumerate(self.var_names):
                combo_y.addItem(f"{j+1}: {v}", j)
            if m.get("y_var_idx", 0) < len(self.var_names):
                combo_y.setCurrentIndex(m.get("y_var_idx", 0))
            combo_y.currentIndexChanged.connect(lambda idx, row=i: self.update_map(row, "y_var_idx", idx))
            self.table_def.setCellWidget(i, 4, combo_y)
            
        self.table_def.resizeColumnsToContents()
        self.table_def.blockSignals(False)

    def setup_lines_table(self):
        self.table_lines.blockSignals(True)
        self.table_lines.clear()
        self.table_lines.setColumnCount(8)
        self.table_lines.setHorizontalHeaderLabels([
            "Map\nNumber", "Map\nName", "Show\nMap", "Show\nLines",
            "Line\nColor", "Line\nThickness", "Line\nPattern", "Pattern\nLength"
        ])
        
        self.table_lines.setRowCount(len(self.maps))
        self.table_lines.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table_lines.horizontalHeader().setStretchLastSection(True)
        self.table_lines.verticalHeader().setVisible(False)
        
        for i, m in enumerate(self.maps):
            item_num = QTableWidgetItem(str(i+1))
            item_num.setFlags(item_num.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table_lines.setItem(i, 0, item_num)
            
            item_name = QTableWidgetItem(m.get("name", f"Map {i+1}"))
            item_name.setFlags(item_name.flags() & ~Qt.ItemFlag.ItemIsEditable) 
            self.table_lines.setItem(i, 1, item_name)
            
            # Show Map Checkbox
            chk_m = QCheckBox()
            chk_m.setChecked(m.get("show", True))
            chk_m.stateChanged.connect(lambda state, row=i: self.update_map(row, "show", state == Qt.CheckState.Checked.value))
            w_m = QWidget(); l_m = QHBoxLayout(w_m); l_m.addWidget(chk_m); l_m.setAlignment(Qt.AlignmentFlag.AlignCenter); l_m.setContentsMargins(0,0,0,0)
            self.table_lines.setCellWidget(i, 2, w_m)
            
            # Show Lines Checkbox
            chk_l = QCheckBox()
            chk_l.setChecked(m.get("show_lines", True))
            chk_l.stateChanged.connect(lambda state, row=i: self.update_map(row, "show_lines", state == Qt.CheckState.Checked.value))
            w_l = QWidget(); l_l = QHBoxLayout(w_l); l_l.addWidget(chk_l); l_l.setAlignment(Qt.AlignmentFlag.AlignCenter); l_l.setContentsMargins(0,0,0,0)
            self.table_lines.setCellWidget(i, 3, w_l)
            
            # Line Color Block
            btn_color = QPushButton()
            c = m.get("color", "#000000")
            btn_color.setStyleSheet(f"background-color: {c}; border: 1px solid #aaa; border-radius: 0px;")
            btn_color.setMinimumSize(40, 20)
            btn_color.clicked.connect(lambda checked, row=i: self.pick_color(row))
            self.table_lines.setCellWidget(i, 4, btn_color)
            
            # Line Thickness
            combo_thick = QComboBox()
            combo_thick.addItems(["0.10%", "0.20%", "0.40%", "0.80%"])
            w_val = m.get("line_width", 2)
            if w_val == 1: combo_thick.setCurrentText("0.10%")
            elif w_val == 2: combo_thick.setCurrentText("0.20%")
            elif w_val == 4: combo_thick.setCurrentText("0.40%")
            elif w_val >= 8: combo_thick.setCurrentText("0.80%")
            combo_thick.currentTextChanged.connect(lambda text, row=i: self.update_thickness(row, text))
            self.table_lines.setCellWidget(i, 5, combo_thick)
            
            # Line Pattern
            combo_style = QComboBox()
            combo_style.addItems(["Solid", "Dashed", "Dotted"])
            combo_style.setCurrentText(m.get("line_style", "Solid"))
            combo_style.currentTextChanged.connect(lambda text, row=i: self.update_map(row, "line_style", text))
            self.table_lines.setCellWidget(i, 6, combo_style)
            
            # Pattern Length
            combo_len = QComboBox()
            combo_len.addItems(["1.00%", "2.00%", "3.00%", "4.00%"])
            combo_len.setCurrentText(m.get("pattern_length", "2.00%"))
            combo_len.currentTextChanged.connect(lambda text, row=i: self.update_map(row, "pattern_length", text))
            self.table_lines.setCellWidget(i, 7, combo_len)
            
        self.table_lines.resizeColumnsToContents()
        self.table_lines.blockSignals(False)

    def setup_curves_table(self):
        self.table_curves.blockSignals(True)
        self.table_curves.clear()
        self.table_curves.setColumnCount(9)
        self.table_curves.setHorizontalHeaderLabels([
            "Map\nNumber", "Map\nName", "Show\nMap",
            "Curve\nType", "Dependent\nVariable", "Curve\nPoints", "Curve\nSetting", "Show\nEquation", "Show\nR²"
        ])
        
        self.table_curves.setRowCount(len(self.maps))
        self.table_curves.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table_curves.horizontalHeader().setStretchLastSection(True)
        self.table_curves.verticalHeader().setVisible(False)
        
        for i, m in enumerate(self.maps):
            # 0: Map Number
            item_num = QTableWidgetItem(str(i+1))
            item_num.setFlags(item_num.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table_curves.setItem(i, 0, item_num)
            
            # 1: Map Name
            item_name = QTableWidgetItem(m.get("name", f"Map {i+1}"))
            item_name.setFlags(item_name.flags() & ~Qt.ItemFlag.ItemIsEditable) 
            self.table_curves.setItem(i, 1, item_name)
            
            # 2: Show Map Checkbox
            chk_m = QCheckBox()
            chk_m.setChecked(m.get("show", True))
            chk_m.stateChanged.connect(lambda state, row=i: self.update_map(row, "show", state == Qt.CheckState.Checked.value))
            w_m = QWidget(); l_m = QHBoxLayout(w_m); l_m.addWidget(chk_m); l_m.setAlignment(Qt.AlignmentFlag.AlignCenter); l_m.setContentsMargins(0,0,0,0)
            self.table_curves.setCellWidget(i, 2, w_m)
            
            # 3: Curve Type Combobox
            combo_type = QComboBox()
            curve_types = [
                "Line segment", "Linear fit", "Polynomial fit", "Exponential fit", 
                "Power fit", "Spline", "Parametric spline", "Akima Spline", 
                "General Curve Fit", "Stineman Interpolation"
            ]
            combo_type.addItems(curve_types)
            # Default to "Line segment" explicitly matching user screenshot
            combo_type.setCurrentText(m.get("curve_type", "Line segment"))
            combo_type.currentTextChanged.connect(lambda text, row=i: self.update_map(row, "curve_type", text))
            if m.get("curve_type", "Line segment") == "Line segment":
                # Color the combo box background a little bit light blue when active 
                pass # keeping native PyQt styling for now
            self.table_curves.setCellWidget(i, 3, combo_type)
            
            # 4: Dependent Variable
            dep_var = QTableWidgetItem(m.get("dependent_var", "Auto"))
            dep_var.setFlags(dep_var.flags() & ~Qt.ItemFlag.ItemIsEditable)
            # Usually only editable if fit chosen? keeping read-only for now
            self.table_curves.setItem(i, 4, dep_var)
            
            # 5: Curve Points
            points_var = QTableWidgetItem(str(m.get("curve_points", "N/A")))
            points_var.setFlags(points_var.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table_curves.setItem(i, 5, points_var)
            
            # 6: Curve Setting
            set_var = QTableWidgetItem(m.get("curve_setting", "N/A"))
            set_var.setFlags(set_var.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table_curves.setItem(i, 6, set_var)
            
            # 7: Show Equation
            chk_eq = QCheckBox()
            chk_eq.setChecked(m.get("show_equation", False))
            chk_eq.stateChanged.connect(lambda state, row=i: self.update_map(row, "show_equation", state == Qt.CheckState.Checked.value))
            w_eq = QWidget()
            l_eq = QHBoxLayout(w_eq)
            l_eq.addWidget(chk_eq)
            l_eq.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l_eq.setContentsMargins(0,0,0,0)
            self.table_curves.setCellWidget(i, 7, w_eq)
            
            # 8: Show R²
            chk_r2 = QCheckBox()
            chk_r2.setChecked(m.get("show_r_squared", False))
            chk_r2.stateChanged.connect(lambda state, row=i: self.update_map(row, "show_r_squared", state == Qt.CheckState.Checked.value))
            w_r2 = QWidget()
            l_r2 = QHBoxLayout(w_r2)
            l_r2.addWidget(chk_r2)
            l_r2.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l_r2.setContentsMargins(0,0,0,0)
            self.table_curves.setCellWidget(i, 8, w_r2)
            
        self.table_curves.resizeColumnsToContents()
        self.table_curves.blockSignals(False)

    def setup_symbols_table(self):
        self.table_symbols.blockSignals(True)
        self.table_symbols.clear()
        self.table_symbols.setColumnCount(11)
        self.table_symbols.setHorizontalHeaderLabels([
            "Map\nNumber", "Map\nName", "Show\nMap", "Show\nSymbols",
            "Symbol\nShape", "Symbol\nSize", "Symbol\nSpacing",
            "Outline\nColor", "Line\nThickness", "Fill\nMode", "Fill\nColor"
        ])
        
        self.table_symbols.setRowCount(len(self.maps))
        self.table_symbols.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table_symbols.horizontalHeader().setStretchLastSection(True)
        self.table_symbols.verticalHeader().setVisible(False)
        
        for i, m in enumerate(self.maps):
            # 0: Map Number
            item_num = QTableWidgetItem(str(i+1))
            item_num.setFlags(item_num.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table_symbols.setItem(i, 0, item_num)
            
            # 1: Map Name
            item_name = QTableWidgetItem(m.get("name", f"Map {i+1}"))
            item_name.setFlags(item_name.flags() & ~Qt.ItemFlag.ItemIsEditable) 
            self.table_symbols.setItem(i, 1, item_name)
            
            # 2: Show Map Checkbox
            chk_m = QCheckBox()
            chk_m.setChecked(m.get("show", True))
            chk_m.stateChanged.connect(lambda state, row=i: self.update_map(row, "show", state == Qt.CheckState.Checked.value))
            w_m = QWidget(); l_m = QHBoxLayout(w_m); l_m.addWidget(chk_m); l_m.setAlignment(Qt.AlignmentFlag.AlignCenter); l_m.setContentsMargins(0,0,0,0)
            self.table_symbols.setCellWidget(i, 2, w_m)
            
            # 3: Show Symbols Checkbox
            chk_s = QCheckBox()
            chk_s.setChecked(m.get("show_symbols", True))
            chk_s.stateChanged.connect(lambda state, row=i: self.update_map(row, "show_symbols", state == Qt.CheckState.Checked.value))
            w_s = QWidget(); l_s = QHBoxLayout(w_s); l_s.addWidget(chk_s); l_s.setAlignment(Qt.AlignmentFlag.AlignCenter); l_s.setContentsMargins(0,0,0,0)
            self.table_symbols.setCellWidget(i, 3, w_s)
            
            # 4: Symbol Shape
            combo_shape = QComboBox()
            combo_shape.addItems(["Square", "Delta", "Diamond", "Circle", "Cross", "Plus", "Star"])
            combo_shape.setCurrentText(m.get("symbol_shape", "Square"))
            combo_shape.currentTextChanged.connect(lambda text, row=i: self.update_map(row, "symbol_shape", text))
            self.table_symbols.setCellWidget(i, 4, combo_shape)
            
            # 5: Symbol Size
            combo_size = QComboBox()
            combo_size.addItems(["1.00%", "2.00%", "2.50%", "3.00%", "5.00%"])
            combo_size.setCurrentText(m.get("symbol_size", "2.50%"))
            combo_size.currentTextChanged.connect(lambda text, row=i: self.update_map(row, "symbol_size", text))
            self.table_symbols.setCellWidget(i, 5, combo_size)
            
            # 6: Symbol Spacing
            combo_spacing = QComboBox()
            combo_spacing.addItems(["Draw all", "Draw every 2nd", "Draw every 5th", "Draw every 10th"])
            combo_spacing.setCurrentText(m.get("symbol_spacing", "Draw all"))
            combo_spacing.currentTextChanged.connect(lambda text, row=i: self.update_map(row, "symbol_spacing", text))
            self.table_symbols.setCellWidget(i, 6, combo_spacing)
            
            # 7: Outline Color
            btn_outline = QPushButton()
            c_out = m.get("symbol_outline_color", m.get("color", "#000000"))
            btn_outline.setStyleSheet(f"background-color: {c_out}; border: 1px solid #aaa; border-radius: 0px;")
            btn_outline.setMinimumSize(40, 20)
            btn_outline.clicked.connect(lambda checked, row=i: self.pick_symbol_color(row, "symbol_outline_color", 7))
            self.table_symbols.setCellWidget(i, 7, btn_outline)
            
            # 8: Line Thickness
            combo_thick = QComboBox()
            combo_thick.addItems(["0.10%", "0.20%", "0.40%", "0.80%"])
            combo_thick.setCurrentText(m.get("symbol_thickness", "0.10%"))
            combo_thick.currentTextChanged.connect(lambda text, row=i: self.update_map(row, "symbol_thickness", text))
            self.table_symbols.setCellWidget(i, 8, combo_thick)
            
            # 9: Fill Mode
            combo_fill = QComboBox()
            combo_fill.addItems(["None", "Specific Color", "Match Base Color"])
            combo_fill.setCurrentText(m.get("symbol_fill_mode", "None"))
            combo_fill.currentTextChanged.connect(lambda text, row=i: self.update_map(row, "symbol_fill_mode", text))
            self.table_symbols.setCellWidget(i, 9, combo_fill)
            
            # 10: Fill Color
            btn_fill = QPushButton()
            c_fill = m.get("symbol_fill_color", "#e0e0e0")
            btn_fill.setStyleSheet(f"background-color: {c_fill}; border: 1px dashed #aaa; border-radius: 0px;")
            btn_fill.setMinimumSize(40, 20)
            btn_fill.clicked.connect(lambda checked, row=i: self.pick_symbol_color(row, "symbol_fill_color", 10))
            self.table_symbols.setCellWidget(i, 10, btn_fill)
            
        self.table_symbols.resizeColumnsToContents()
        self.table_symbols.blockSignals(False)

    def setup_errorbars_table(self):
        self.table_errorbars.blockSignals(True)
        self.table_errorbars.clear()
        self.table_errorbars.setColumnCount(10)
        self.table_errorbars.setHorizontalHeaderLabels([
            "Map\nNumber", "Map\nName", "Show\nMap", "Show\nError Bars",
            "Error Bar\nVariable", "Error Bar\nType", "Error Bar\nSpacing",
            "Error Bar\nColor", "Error Bar\nSize", "Line\nThickness"
        ])
        
        self.table_errorbars.setRowCount(len(self.maps))
        self.table_errorbars.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table_errorbars.horizontalHeader().setStretchLastSection(True)
        self.table_errorbars.verticalHeader().setVisible(False)
        
        for i, m in enumerate(self.maps):
            # 0: Map Number
            item_num = QTableWidgetItem(str(i+1))
            item_num.setFlags(item_num.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table_errorbars.setItem(i, 0, item_num)
            
            # 1: Map Name
            item_name = QTableWidgetItem(m.get("name", f"Map {i+1}"))
            item_name.setFlags(item_name.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table_errorbars.setItem(i, 1, item_name)
            
            # 2: Show Map Checkbox
            chk_m = QCheckBox()
            chk_m.setChecked(m.get("show", True))
            chk_m.stateChanged.connect(lambda state, row=i: self.update_map(row, "show", state == Qt.CheckState.Checked.value))
            w_m = QWidget(); l_m = QHBoxLayout(w_m); l_m.addWidget(chk_m); l_m.setAlignment(Qt.AlignmentFlag.AlignCenter); l_m.setContentsMargins(0,0,0,0)
            self.table_errorbars.setCellWidget(i, 2, w_m)
            
            # 3: Show Error Bars Checkbox
            chk_eb = QCheckBox()
            chk_eb.setChecked(m.get("show_error_bars", False))
            chk_eb.stateChanged.connect(lambda state, row=i: self.update_map(row, "show_error_bars", state == Qt.CheckState.Checked.value))
            w_eb = QWidget(); l_eb = QHBoxLayout(w_eb); l_eb.addWidget(chk_eb); l_eb.setAlignment(Qt.AlignmentFlag.AlignCenter); l_eb.setContentsMargins(0,0,0,0)
            self.table_errorbars.setCellWidget(i, 3, w_eb)
            
            # 4: Error Bar Variable (dropdown of all loaded variables)
            combo_var = QComboBox()
            for j, v in enumerate(self.var_names):
                combo_var.addItem(f"{j+1}: {v}", j)
            eb_var_idx = m.get("error_bar_variable_idx", min(2, len(self.var_names) - 1) if self.var_names else 0)
            if eb_var_idx < len(self.var_names):
                combo_var.setCurrentIndex(eb_var_idx)
            combo_var.currentIndexChanged.connect(lambda idx, row=i: self.update_map(row, "error_bar_variable_idx", idx))
            self.table_errorbars.setCellWidget(i, 4, combo_var)
            
            # 5: Error Bar Type
            combo_type = QComboBox()
            combo_type.addItems(["Vertical", "Horizontal", "Both"])
            combo_type.setCurrentText(m.get("error_bar_type", "Vertical"))
            combo_type.currentTextChanged.connect(lambda text, row=i: self.update_map(row, "error_bar_type", text))
            self.table_errorbars.setCellWidget(i, 5, combo_type)
            
            # 6: Error Bar Spacing
            combo_space = QComboBox()
            combo_space.addItems(["Draw all", "Draw every 2nd", "Draw every 5th", "Draw every 10th"])
            combo_space.setCurrentText(m.get("error_bar_spacing", "Draw all"))
            combo_space.currentTextChanged.connect(lambda text, row=i: self.update_map(row, "error_bar_spacing", text))
            self.table_errorbars.setCellWidget(i, 6, combo_space)
            
            # 7: Error Bar Color
            btn_color = QPushButton()
            c_eb = m.get("error_bar_color", m.get("color", "#000000"))
            btn_color.setStyleSheet(f"background-color: {c_eb}; border: 1px solid #aaa; border-radius: 0px;")
            btn_color.setMinimumSize(40, 20)
            btn_color.clicked.connect(lambda checked, row=i: self.pick_errorbar_color(row))
            self.table_errorbars.setCellWidget(i, 7, btn_color)
            
            # 8: Error Bar Size (cap size)
            combo_size = QComboBox()
            combo_size.addItems(["1.00%", "2.00%", "2.50%", "3.00%", "5.00%"])
            combo_size.setCurrentText(m.get("error_bar_size", "2.50%"))
            combo_size.currentTextChanged.connect(lambda text, row=i: self.update_map(row, "error_bar_size", text))
            self.table_errorbars.setCellWidget(i, 8, combo_size)
            
            # 9: Line Thickness
            combo_thick = QComboBox()
            combo_thick.addItems(["0.10%", "0.20%", "0.40%", "0.80%"])
            combo_thick.setCurrentText(m.get("error_bar_line_thickness", "0.10%"))
            combo_thick.currentTextChanged.connect(lambda text, row=i: self.update_map(row, "error_bar_line_thickness", text))
            self.table_errorbars.setCellWidget(i, 9, combo_thick)
            
        self.table_errorbars.resizeColumnsToContents()
        self.table_errorbars.blockSignals(False)

    def pick_symbol_color(self, row, key, col):
        color = QColorDialog.getColor()
        if color.isValid():
            self.update_map(row, key, color.name())
            btn = self.table_symbols.cellWidget(row, col)
            style = "solid" if key == "symbol_outline_color" else "dashed"
            if btn: btn.setStyleSheet(f"background-color: {color.name()}; border: 1px {style} #aaa; border-radius: 0px;")

    def pick_errorbar_color(self, row):
        color = QColorDialog.getColor()
        if color.isValid():
            self.update_map(row, "error_bar_color", color.name())
            btn = self.table_errorbars.cellWidget(row, 7)
            if btn: btn.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #aaa; border-radius: 0px;")

    def update_thickness(self, row, text):
        val = 2
        if text == "0.10%": val = 1
        elif text == "0.20%": val = 2
        elif text == "0.40%": val = 4
        elif text == "0.80%": val = 8
        self.update_map(row, "line_width", val)

    def pick_color(self, row):
        color = QColorDialog.getColor()
        if color.isValid():
            self.update_map(row, "color", color.name())
            btn = self.table_lines.cellWidget(row, 4)
            if btn: btn.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #aaa; border-radius: 0px;")
                
    def update_map(self, row, key, value):
        if row < len(self.maps):
            self.maps[row][key] = value
            
    def create_map(self):
        new_map = {
            "show": True,
            "show_lines": True,
            "name": f"Map {len(self.maps) + 1}",
            "x_var_idx": 0,
            "y_var_idx": min(1, len(self.var_names) - 1) if self.var_names else 0,
            "color": "#ff7f0e",
            "line_style": "Solid",
            "line_width": 2,
            "pattern_length": "2.00%",
            "curve_type": "Line segment",
            "dependent_var": "Auto",
            "curve_points": "N/A",
            "curve_setting": "N/A",
            "show_equation": False,
            "show_r_squared": False,
            "show_symbols": True,
            "symbol_shape": "Square",
            "symbol_size": "2.50%",
            "symbol_spacing": "Draw all",
            "symbol_outline_color": "#ff7f0e",
            "symbol_thickness": "0.10%",
            "symbol_fill_mode": "None",
            "symbol_fill_color": "#ffffff",
            "show_error_bars": False,
            "error_bar_variable_idx": min(2, len(self.var_names) - 1) if self.var_names else 0,
            "error_bar_type": "Vertical",
            "error_bar_spacing": "Draw all",
            "error_bar_color": "#ff7f0e",
            "error_bar_size": "2.50%",
            "error_bar_line_thickness": "0.10%"
        }
        self.maps.append(new_map)
        self.setup_tables()
        
    def delete_map(self):
        idx = self.tabs.currentIndex()
        if idx == 0: curr_table = self.table_def
        elif idx == 1: curr_table = self.table_lines
        elif idx == 2: curr_table = self.table_curves
        elif idx == 3: curr_table = self.table_symbols
        else: curr_table = self.table_errorbars
        
        row = curr_table.currentRow()
        if 0 <= row < len(self.maps):
            self.maps.pop(row)
            self.setup_tables()

