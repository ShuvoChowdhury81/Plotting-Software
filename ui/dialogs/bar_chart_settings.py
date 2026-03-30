import copy
from PyQt6.QtWidgets import (QDialog, QWidget, QVBoxLayout, QHBoxLayout,
                             QTabWidget, QLabel, QComboBox, QPushButton,
                             QDoubleSpinBox, QCheckBox, QFormLayout,
                             QSlider, QGroupBox, QColorDialog, QLineEdit,
                             QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt


class BarChartSettingsDialog(QDialog):
    """Dialog for configuring bar chart visual options and data mapping."""

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Bar Chart Settings")
        self.resize(580, 480)
        self.parent_window = parent
        self.cfg = copy.deepcopy(parent.bar_chart_cfg)
        self.maps = copy.deepcopy(parent.maps)

        layout = QVBoxLayout(self)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabBar::tab { padding: 8px 15px; border: 1px solid #dcdcdc; border-bottom: none; background: #f0f0f0; color: #333; }
            QTabBar::tab:selected { background: white; font-weight: bold; border-top: 2px solid #1f77b4; }
            QTabWidget::pane { border: 1px solid #dcdcdc; }
        """)
        layout.addWidget(self.tabs)

        self._build_data_selection_tab()
        self._build_visual_tab()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_apply = QPushButton("Apply")
        btn_apply.clicked.connect(self.apply_changes)
        btn_layout.addWidget(btn_apply)

        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.accept_changes)
        btn_ok.setDefault(True)
        btn_layout.addWidget(btn_ok)

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.close)
        btn_layout.addWidget(btn_close)

        layout.addLayout(btn_layout)

    # ─── Data Selection Tab ──────────────────────────────────────────────

    def _build_data_selection_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        lbl = QLabel("Configure which variables each mapping uses for the bar chart.\n"
                      "X variable provides bar labels/categories, Y variable provides bar heights.")
        lbl.setWordWrap(True)
        layout.addWidget(lbl)

        self.table_data = QTableWidget()
        self.table_data.setColumnCount(6)
        self.table_data.setHorizontalHeaderLabels([
            "Map\nNumber", "Map\nName", "Show", "X Variable\n(Categories)",
            "Y Variable\n(Heights)", "Color"
        ])
        self.table_data.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table_data.horizontalHeader().setStretchLastSection(True)
        self.table_data.verticalHeader().setVisible(False)

        self.table_data.setRowCount(len(self.maps))
        self._color_buttons = []

        _btn_style = "border: 1px solid #aaa; border-radius: 0px; min-height: 20px; min-width: 40px;"

        for i, m in enumerate(self.maps):
            # Col 0: Map Number
            item_num = QTableWidgetItem(str(i + 1))
            item_num.setFlags(item_num.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table_data.setItem(i, 0, item_num)

            # Col 1: Map Name
            item_name = QTableWidgetItem(m.get("name", f"Map {i+1}"))
            item_name.setFlags(item_name.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table_data.setItem(i, 1, item_name)

            # Col 2: Show checkbox
            chk_show = QCheckBox()
            chk_show.setChecked(m.get("show", True))
            chk_show.stateChanged.connect(lambda state, row=i: self._update_map(row, "show", state == Qt.CheckState.Checked.value))
            w_show = QWidget(); l_show = QHBoxLayout(w_show)
            l_show.addWidget(chk_show); l_show.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l_show.setContentsMargins(0, 0, 0, 0)
            self.table_data.setCellWidget(i, 2, w_show)

            # Col 3: X Variable (categories)
            combo_x = QComboBox()
            for j, v in enumerate(self.parent_window.var_names):
                combo_x.addItem(f"{j+1}: {v}", j)
            x_idx = m.get("bar_x_var_idx", m.get("x_var_idx", 0))
            if x_idx < combo_x.count():
                combo_x.setCurrentIndex(x_idx)
            combo_x.currentIndexChanged.connect(lambda idx, row=i: self._update_map(row, "bar_x_var_idx", idx))
            self.table_data.setCellWidget(i, 3, combo_x)

            # Col 4: Y Variable (heights)
            combo_y = QComboBox()
            for j, v in enumerate(self.parent_window.var_names):
                combo_y.addItem(f"{j+1}: {v}", j)
            y_idx = m.get("bar_y_var_idx", m.get("y_var_idx", 0))
            if y_idx < combo_y.count():
                combo_y.setCurrentIndex(y_idx)
            combo_y.currentIndexChanged.connect(lambda idx, row=i: self._update_map(row, "bar_y_var_idx", idx))
            self.table_data.setCellWidget(i, 4, combo_y)

            # Col 5: Color button
            color = m.get("color", "#1f77b4")
            btn_color = QPushButton()
            btn_color.setStyleSheet(f"background-color: {color}; {_btn_style}")
            btn_color.clicked.connect(lambda _, row=i: self._pick_map_color(row))
            self.table_data.setCellWidget(i, 5, btn_color)
            self._color_buttons.append(btn_color)

        self.table_data.resizeColumnsToContents()
        layout.addWidget(self.table_data)

        self.tabs.addTab(tab, "Data Selection")

    def _update_map(self, row, key, value):
        if row < len(self.maps):
            self.maps[row][key] = value

    def _pick_map_color(self, row):
        from PyQt6.QtGui import QColor
        current = self.maps[row].get("color", "#1f77b4")
        color = QColorDialog.getColor(QColor(current), self, f"Bar Color — Map {row+1}")
        if color.isValid():
            self.maps[row]["color"] = color.name()
            self._color_buttons[row].setStyleSheet(
                f"background-color: {color.name()}; border: 1px solid #aaa; border-radius: 0px; min-height: 20px; min-width: 40px;"
            )

    # ─── Visual Style Tab ────────────────────────────────────────────────

    def _build_visual_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        _btn_color_style = "border: 1px solid #aaa; border-radius: 0px; min-height: 22px;"

        # Bar Style
        grp_style = QGroupBox("Bar Style")
        form = QFormLayout(grp_style)

        self.cb_orientation = QComboBox()
        self.cb_orientation.addItems(["Vertical", "Horizontal"])
        self.cb_orientation.setCurrentText(self.cfg.get("orientation", "Vertical"))
        form.addRow("Orientation:", self.cb_orientation)

        self.cb_group_mode = QComboBox()
        self.cb_group_mode.addItems(["Grouped", "Stacked"])
        self.cb_group_mode.setCurrentText(self.cfg.get("group_mode", "Grouped"))
        form.addRow("Group Mode:", self.cb_group_mode)

        # Bar width slider
        width_widget = QWidget()
        width_layout = QHBoxLayout(width_widget)
        width_layout.setContentsMargins(0, 0, 0, 0)
        self.slider_bar_width = QSlider(Qt.Orientation.Horizontal)
        self.slider_bar_width.setRange(10, 100)  # 0.1 to 1.0
        self.slider_bar_width.setValue(int(self.cfg.get("bar_width", 0.8) * 100))
        self.lbl_bar_width_val = QLabel(f"{self.cfg.get('bar_width', 0.8):.2f}")
        self.slider_bar_width.valueChanged.connect(lambda v: self.lbl_bar_width_val.setText(f"{v/100:.2f}"))
        width_layout.addWidget(self.slider_bar_width)
        width_layout.addWidget(self.lbl_bar_width_val)
        form.addRow("Bar Width:", width_widget)

        # Alpha slider
        alpha_widget = QWidget()
        alpha_layout = QHBoxLayout(alpha_widget)
        alpha_layout.setContentsMargins(0, 0, 0, 0)
        self.slider_alpha = QSlider(Qt.Orientation.Horizontal)
        self.slider_alpha.setRange(0, 100)
        self.slider_alpha.setValue(int(self.cfg.get("alpha", 0.85) * 100))
        self.lbl_alpha_val = QLabel(f"{self.cfg.get('alpha', 0.85):.2f}")
        self.slider_alpha.valueChanged.connect(lambda v: self.lbl_alpha_val.setText(f"{v/100:.2f}"))
        alpha_layout.addWidget(self.slider_alpha)
        alpha_layout.addWidget(self.lbl_alpha_val)
        form.addRow("Transparency:", alpha_widget)

        layout.addWidget(grp_style)

        # Colors
        grp_colors = QGroupBox("Edge & Annotations")
        color_form = QFormLayout(grp_colors)

        # Edge color button
        self.btn_edge_color = QPushButton()
        edge_c = self.cfg.get("edge_color", "#333333")
        self.btn_edge_color.setStyleSheet(f"background-color: {edge_c}; {_btn_color_style}")
        self.btn_edge_color.clicked.connect(self._pick_edge_color)
        self._edge_color = edge_c
        color_form.addRow("Edge Color:", self.btn_edge_color)

        self.spin_edge_width = QDoubleSpinBox()
        self.spin_edge_width.setRange(0.0, 5.0)
        self.spin_edge_width.setSingleStep(0.1)
        self.spin_edge_width.setValue(self.cfg.get("edge_width", 0.8))
        color_form.addRow("Edge Width:", self.spin_edge_width)

        # Show value labels
        self.chk_show_values = QCheckBox("Show value labels on bars")
        self.chk_show_values.setChecked(self.cfg.get("show_values", False))
        self.chk_show_values.toggled.connect(self._on_show_values_toggled)
        color_form.addRow(self.chk_show_values)

        self.le_value_fmt = QLineEdit(self.cfg.get("value_fmt", "{:.2g}"))
        self.le_value_fmt.setPlaceholderText("{:.2g}")
        self.le_value_fmt.setEnabled(self.cfg.get("show_values", False))
        color_form.addRow("Value Format:", self.le_value_fmt)

        layout.addWidget(grp_colors)
        layout.addStretch()

        self.tabs.addTab(tab, "Visual Style")

    def _on_show_values_toggled(self, checked):
        self.le_value_fmt.setEnabled(checked)

    def _pick_edge_color(self):
        from PyQt6.QtGui import QColor
        color = QColorDialog.getColor(QColor(self._edge_color), self, "Select Edge Color")
        if color.isValid():
            self._edge_color = color.name()
            self.btn_edge_color.setStyleSheet(
                f"background-color: {color.name()}; border: 1px solid #aaa; border-radius: 0px; min-height: 22px;"
            )

    # ─── Config collection ───────────────────────────────────────────────

    def _collect_cfg(self):
        cfg = {}
        cfg["orientation"] = self.cb_orientation.currentText()
        cfg["group_mode"] = self.cb_group_mode.currentText()
        cfg["bar_width"] = self.slider_bar_width.value() / 100.0
        cfg["alpha"] = self.slider_alpha.value() / 100.0
        cfg["edge_color"] = self._edge_color
        cfg["edge_width"] = self.spin_edge_width.value()
        cfg["show_values"] = self.chk_show_values.isChecked()
        cfg["value_fmt"] = self.le_value_fmt.text().strip() or "{:.2g}"
        cfg["bar_color"] = self.cfg.get("bar_color")  # preserve if set externally
        return cfg

    # ─── Apply / OK ──────────────────────────────────────────────────────

    def apply_changes(self):
        self.parent_window.bar_chart_cfg = self._collect_cfg()
        self.parent_window.maps = copy.deepcopy(self.maps)
        self.parent_window.update_plot()

    def accept_changes(self):
        self.apply_changes()
        self.close()
