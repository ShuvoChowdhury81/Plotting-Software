"""Dialog for creating a new mapping — either by selecting variables or defining an equation."""

import numpy as np
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLabel, QComboBox, QPushButton, QLineEdit,
                             QGroupBox, QRadioButton, QButtonGroup, QTextEdit,
                             QMessageBox, QColorDialog, QSpinBox, QDoubleSpinBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor


# Default color palette for new maps
_COLORS = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
]


class CreateMapDialog(QDialog):
    """Dialog for creating a new mapping from variable selection or equation."""

    def __init__(self, parent, var_names, data_vars, existing_map_count=0):
        super().__init__(parent)
        self.setWindowTitle("Create New Map")
        self.resize(520, 420)
        self.var_names = var_names
        self.data_vars = data_vars
        self.result_map = None  # Set if accepted

        # Pick a default color from the palette
        self._color = _COLORS[existing_map_count % len(_COLORS)]

        layout = QVBoxLayout(self)

        # Map Name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Map Name:"))
        self.le_name = QLineEdit(f"Map {existing_map_count + 1}")
        name_layout.addWidget(self.le_name)
        layout.addLayout(name_layout)

        # Color picker
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Color:"))
        self.btn_color = QPushButton()
        self.btn_color.setStyleSheet(
            f"background-color: {self._color}; border: 1px solid #aaa; min-height: 22px; min-width: 60px;"
        )
        self.btn_color.clicked.connect(self._pick_color)
        color_layout.addWidget(self.btn_color)
        color_layout.addStretch()
        layout.addLayout(color_layout)

        # Mode selection
        self.rb_variable = QRadioButton("From Variables")
        self.rb_equation = QRadioButton("From Equation")
        self.rb_variable.setChecked(True)
        mode_group = QButtonGroup(self)
        mode_group.addButton(self.rb_variable)
        mode_group.addButton(self.rb_equation)
        self.rb_variable.toggled.connect(self._on_mode_changed)

        mode_layout = QHBoxLayout()
        mode_layout.addWidget(self.rb_variable)
        mode_layout.addWidget(self.rb_equation)
        mode_layout.addStretch()
        layout.addLayout(mode_layout)

        # === Variable Selection panel ===
        self.grp_vars = QGroupBox("Select Variables")
        var_form = QFormLayout(self.grp_vars)

        self.cb_x_var = QComboBox()
        self.cb_y_var = QComboBox()
        for j, v in enumerate(var_names):
            self.cb_x_var.addItem(f"{j+1}: {v}", j)
            self.cb_y_var.addItem(f"{j+1}: {v}", j)
        if len(var_names) > 1:
            self.cb_y_var.setCurrentIndex(1)

        var_form.addRow("X Variable:", self.cb_x_var)
        var_form.addRow("Y Variable:", self.cb_y_var)
        layout.addWidget(self.grp_vars)

        # === Equation panel ===
        self.grp_eq = QGroupBox("Define by Equation")
        eq_layout = QVBoxLayout(self.grp_eq)

        help_text = (
            "Write a NumPy expression. Available variables:\n"
            "  • x1 — a standalone axis variable (range defined below)\n"
            "  • v1, v2, v3, … — your loaded data columns by index\n"
            "  • Column names are also available (e.g., Time, Velocity)\n"
            "  • NumPy functions: sin, cos, exp, log, sqrt, etc.\n\n"
            "Examples (no data needed):\n"
            "  X = x1          Y = sin(x1)\n"
            "  X = x1          Y = x1**2 - 3*x1 + 1\n\n"
            "Examples (using loaded data):\n"
            "  X = v1           Y = v2 / v3"
        )
        lbl_help = QLabel(help_text)
        lbl_help.setWordWrap(True)
        lbl_help.setStyleSheet(
            "background-color: #f5f5f0; color: #444; padding: 8px; "
            "border: 1px solid #dcdcdc; border-radius: 4px; font-size: 10pt;"
        )
        eq_layout.addWidget(lbl_help)

        # Range controls for x1
        range_grp = QGroupBox("x1 Range")
        range_form = QFormLayout(range_grp)
        self.spin_x_start = QDoubleSpinBox()
        self.spin_x_start.setRange(-1e9, 1e9)
        self.spin_x_start.setDecimals(3)
        self.spin_x_start.setValue(0.0)
        range_form.addRow("Start:", self.spin_x_start)

        self.spin_x_end = QDoubleSpinBox()
        self.spin_x_end.setRange(-1e9, 1e9)
        self.spin_x_end.setDecimals(3)
        self.spin_x_end.setValue(10.0)
        range_form.addRow("End:", self.spin_x_end)

        self.spin_x_points = QSpinBox()
        self.spin_x_points.setRange(2, 100000)
        self.spin_x_points.setValue(200)
        range_form.addRow("Points:", self.spin_x_points)
        eq_layout.addWidget(range_grp)

        eq_form = QFormLayout()
        self.le_x_eq = QLineEdit("x1")
        self.le_y_eq = QLineEdit("sin(x1)")
        eq_form.addRow("X =", self.le_x_eq)
        eq_form.addRow("Y =", self.le_y_eq)
        eq_layout.addLayout(eq_form)

        # Preview label
        self.lbl_preview = QLabel("")
        self.lbl_preview.setStyleSheet("color: #666; font-style: italic;")
        eq_layout.addWidget(self.lbl_preview)

        layout.addWidget(self.grp_eq)
        self.grp_eq.setVisible(False)

        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_create = QPushButton("Create")
        btn_create.setDefault(True)
        btn_create.clicked.connect(self._on_create)
        btn_layout.addWidget(btn_create)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        layout.addLayout(btn_layout)

    def _pick_color(self):
        color = QColorDialog.getColor(QColor(self._color), self, "Map Color")
        if color.isValid():
            self._color = color.name()
            self.btn_color.setStyleSheet(
                f"background-color: {self._color}; border: 1px solid #aaa; min-height: 22px; min-width: 60px;"
            )

    def _on_mode_changed(self, checked):
        self.grp_vars.setVisible(self.rb_variable.isChecked())
        self.grp_eq.setVisible(self.rb_equation.isChecked())

    def _build_eval_namespace(self):
        """Build a namespace dict for evaluating equations."""
        ns = {"np": np, "__builtins__": {}}
        # Add math functions directly
        for fn in ["sin", "cos", "tan", "exp", "log", "log10", "sqrt",
                    "abs", "pi", "e", "arcsin", "arccos", "arctan",
                    "sinh", "cosh", "tanh", "floor", "ceil",
                    "linspace", "arange", "zeros", "ones"]:
            if hasattr(np, fn):
                ns[fn] = getattr(np, fn)

        # Standalone axis variable x1
        x_start = self.spin_x_start.value()
        x_end = self.spin_x_end.value()
        x_pts = self.spin_x_points.value()
        ns["x1"] = np.linspace(x_start, x_end, x_pts)

        # Add loaded data as v1, v2, ...
        for j, arr in enumerate(self.data_vars):
            ns[f"v{j+1}"] = np.asarray(arr, dtype=float)

        # Also add by column name (sanitised — only valid Python identifiers)
        for j, name in enumerate(self.var_names):
            safe = name.replace(" ", "_").replace("-", "_")
            if safe.isidentifier():
                ns[safe] = np.asarray(self.data_vars[j], dtype=float)

        return ns

    def _on_create(self):
        name = self.le_name.text().strip() or "NewMap"
        color = self._color

        if self.rb_variable.isChecked():
            # Simple variable selection
            x_idx = self.cb_x_var.currentData()
            y_idx = self.cb_y_var.currentData()
            self.result_map = self._make_map_dict(name, color, x_idx, y_idx)
            self.accept()
        else:
            # Equation mode
            x_expr = self.le_x_eq.text().strip()
            y_expr = self.le_y_eq.text().strip()
            if not x_expr or not y_expr:
                QMessageBox.warning(self, "Error", "Both X and Y equations are required.")
                return

            try:
                ns = self._build_eval_namespace()
                x_data = np.asarray(eval(x_expr, ns), dtype=float)
                y_data = np.asarray(eval(y_expr, ns), dtype=float)
            except Exception as ex:
                QMessageBox.critical(self, "Equation Error",
                                     f"Could not evaluate equations:\n{ex}")
                return

            if x_data.ndim == 0:
                n = self.spin_x_points.value()
                x_data = np.full(n, x_data)
            if y_data.ndim == 0:
                y_data = np.full(len(x_data), y_data)

            # Ensure same length
            min_len = min(len(x_data), len(y_data))
            x_data = x_data[:min_len]
            y_data = y_data[:min_len]

            # Store the computed data as new variables in the parent
            x_name = f"eq_x ({x_expr})"
            y_name = f"eq_y ({y_expr})"

            self.result_map = self._make_map_dict(name, color, -1, -1)
            self.result_map["_eq_x_data"] = x_data
            self.result_map["_eq_y_data"] = y_data
            self.result_map["_eq_x_name"] = x_name
            self.result_map["_eq_y_name"] = y_name
            self.result_map["_eq_x_expr"] = x_expr
            self.result_map["_eq_y_expr"] = y_expr

            self.accept()

    @staticmethod
    def _make_map_dict(name, color, x_idx, y_idx):
        return {
            "show": True,
            "show_lines": True,
            "name": name,
            "x_var_idx": x_idx,
            "y_var_idx": y_idx,
            "color": color,
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
            "symbol_outline_color": color,
            "symbol_thickness": "0.10%",
            "symbol_fill_mode": "None",
            "symbol_fill_color": "#ffffff",
            "show_error_bars": False,
            "error_bar_variable_idx": 0,
            "error_bar_type": "Vertical",
            "error_bar_spacing": "Draw all",
            "error_bar_color": color,
            "error_bar_size": "2.50%",
            "error_bar_line_thickness": "0.10%",
        }
