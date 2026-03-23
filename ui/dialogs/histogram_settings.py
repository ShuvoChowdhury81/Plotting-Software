import copy
from PyQt6.QtWidgets import (QDialog, QWidget, QVBoxLayout, QHBoxLayout,
                             QTabWidget, QLabel, QComboBox, QPushButton,
                             QSpinBox, QDoubleSpinBox, QCheckBox, QFormLayout,
                             QSlider, QGroupBox, QColorDialog, QLineEdit,
                             QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt


class HistogramSettingsDialog(QDialog):
    """Dialog for configuring histogram binning, normalization, and visual options."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Histogram Settings")
        self.resize(580, 480)
        self.parent_window = parent
        self.cfg = copy.deepcopy(parent.histogram_cfg)
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
        self._build_binning_tab()
        self._build_normalization_tab()
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
    
    def _build_data_selection_tab(self):
        """Tab for selecting which variable each mapping uses for the histogram."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        lbl = QLabel("Configure which variable each mapping uses for the histogram,\n"
                      "set its bar color, and toggle per-mapping overlays.")
        lbl.setWordWrap(True)
        layout.addWidget(lbl)
        
        self.table_data = QTableWidget()
        self.table_data.setColumnCount(8)
        self.table_data.setHorizontalHeaderLabels([
            "Map\nNumber", "Map\nName", "Show", "Histogram\nVariable",
            "Color", "KDE", "Mean", "Median"
        ])
        self.table_data.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table_data.horizontalHeader().setStretchLastSection(False)
        self.table_data.verticalHeader().setVisible(False)
        
        self.table_data.setRowCount(len(self.maps))
        self._hist_var_combos = []
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
            
            # Col 2: Show Map checkbox
            chk_show = QCheckBox()
            chk_show.setChecked(m.get("show", True))
            chk_show.stateChanged.connect(lambda state, row=i: self._update_map(row, "show", state == Qt.CheckState.Checked.value))
            w_show = QWidget(); l_show = QHBoxLayout(w_show)
            l_show.addWidget(chk_show); l_show.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l_show.setContentsMargins(0, 0, 0, 0)
            self.table_data.setCellWidget(i, 2, w_show)
            
            # Col 3: Histogram Variable dropdown
            combo = QComboBox()
            for j, v in enumerate(self.parent_window.var_names):
                combo.addItem(f"{j+1}: {v}", j)
            default_idx = m.get("hist_var_idx", m.get("y_var_idx", 0))
            if default_idx < combo.count():
                combo.setCurrentIndex(default_idx)
            combo.currentIndexChanged.connect(lambda idx, row=i: self._update_map(row, "hist_var_idx", idx))
            self.table_data.setCellWidget(i, 3, combo)
            self._hist_var_combos.append(combo)
            
            # Col 4: Color button
            color = m.get("color", "#1f77b4")
            btn_color = QPushButton()
            btn_color.setStyleSheet(f"background-color: {color}; {_btn_style}")
            btn_color.clicked.connect(lambda _, row=i: self._pick_map_color(row))
            self.table_data.setCellWidget(i, 4, btn_color)
            self._color_buttons.append(btn_color)
            
            # Col 5: KDE checkbox
            chk_kde = QCheckBox()
            chk_kde.setChecked(m.get("show_kde", False))
            chk_kde.stateChanged.connect(lambda state, row=i: self._update_map(row, "show_kde", state == Qt.CheckState.Checked.value))
            w_kde = QWidget(); l_kde = QHBoxLayout(w_kde)
            l_kde.addWidget(chk_kde); l_kde.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l_kde.setContentsMargins(0, 0, 0, 0)
            self.table_data.setCellWidget(i, 5, w_kde)
            
            # Col 6: Mean checkbox
            chk_mean = QCheckBox()
            chk_mean.setChecked(m.get("show_mean_line", False))
            chk_mean.stateChanged.connect(lambda state, row=i: self._update_map(row, "show_mean_line", state == Qt.CheckState.Checked.value))
            w_mean = QWidget(); l_mean = QHBoxLayout(w_mean)
            l_mean.addWidget(chk_mean); l_mean.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l_mean.setContentsMargins(0, 0, 0, 0)
            self.table_data.setCellWidget(i, 6, w_mean)
            
            # Col 7: Median checkbox
            chk_med = QCheckBox()
            chk_med.setChecked(m.get("show_median_line", False))
            chk_med.stateChanged.connect(lambda state, row=i: self._update_map(row, "show_median_line", state == Qt.CheckState.Checked.value))
            w_med = QWidget(); l_med = QHBoxLayout(w_med)
            l_med.addWidget(chk_med); l_med.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l_med.setContentsMargins(0, 0, 0, 0)
            self.table_data.setCellWidget(i, 7, w_med)
        
        self.table_data.resizeColumnsToContents()
        layout.addWidget(self.table_data)
        
        self.tabs.addTab(tab, "Data Selection")
    
    def _update_map(self, row, key, value):
        if row < len(self.maps):
            self.maps[row][key] = value
    
    def _pick_map_color(self, row):
        """Open color picker for a mapping's bar color."""
        from PyQt6.QtGui import QColor
        current = self.maps[row].get("color", "#1f77b4")
        color = QColorDialog.getColor(QColor(current), self, f"Bar Color — Map {row+1}")
        if color.isValid():
            self.maps[row]["color"] = color.name()
            self._color_buttons[row].setStyleSheet(
                f"background-color: {color.name()}; border: 1px solid #aaa; border-radius: 0px; min-height: 20px; min-width: 40px;"
            )
    
    def _build_binning_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        math_style = (
            "background-color: #f5f5f0; color: #333; padding: 8px 12px;"
            "border: 1px solid #dcdcdc; border-radius: 4px;"
            "font-family: 'Cambria Math', 'Times New Roman', serif; font-size: 12pt;"
        )
        
        # Binning Method
        grp_method = QGroupBox("Binning Method")
        method_layout = QVBoxLayout(grp_method)
        form = QFormLayout()
        
        self.cb_bin_method = QComboBox()
        self.cb_bin_method.addItems([
            "Auto (Sturges)", "Auto (Scott)", "Auto (Freedman-Diaconis)", "Auto (sqrt)",
            "Manual (Count)", "Manual (Width)", "Integer"
        ])
        self.cb_bin_method.setCurrentText(self.cfg.get("bin_method", "Auto (Sturges)"))
        self.cb_bin_method.currentTextChanged.connect(self._on_bin_method_changed)
        form.addRow("Method:", self.cb_bin_method)
        
        _spin_style = """
            QSpinBox:disabled, QDoubleSpinBox:disabled {
                background-color: #e8e8e8;
                color: #aaaaaa;
            }
        """
        
        # Manual bin count
        self.spin_bin_count = QSpinBox()
        self.spin_bin_count.setRange(1, 1000)
        self.spin_bin_count.setValue(self.cfg.get("bin_count", 10))
        self.spin_bin_count.setStyleSheet(_spin_style)
        form.addRow("Bin Count:", self.spin_bin_count)
        
        # Fixed bin width
        self.spin_bin_width = QDoubleSpinBox()
        self.spin_bin_width.setRange(0.001, 1e9)
        self.spin_bin_width.setDecimals(4)
        self.spin_bin_width.setSingleStep(0.1)
        self.spin_bin_width.setValue(self.cfg.get("bin_width", 1.0))
        self.spin_bin_width.setStyleSheet(_spin_style)
        form.addRow("Bin Width:", self.spin_bin_width)
        
        method_layout.addLayout(form)
        
        # Math formula label for binning method
        self.lbl_bin_math = QLabel()
        self.lbl_bin_math.setWordWrap(True)
        self.lbl_bin_math.setStyleSheet(math_style)
        method_layout.addWidget(self.lbl_bin_math)
        
        layout.addWidget(grp_method)
        
        # Bin Range
        grp_range = QGroupBox("Bin Range (leave blank for auto)")
        range_form = QFormLayout(grp_range)
        
        self.le_bin_min = QLineEdit()
        self.le_bin_min.setPlaceholderText("Auto")
        if self.cfg.get("bin_min") is not None:
            self.le_bin_min.setText(str(self.cfg["bin_min"]))
        range_form.addRow("Min:", self.le_bin_min)
        
        self.le_bin_max = QLineEdit()
        self.le_bin_max.setPlaceholderText("Auto")
        if self.cfg.get("bin_max") is not None:
            self.le_bin_max.setText(str(self.cfg["bin_max"]))
        range_form.addRow("Max:", self.le_bin_max)
        
        layout.addWidget(grp_range)
        layout.addStretch()
        
        self.tabs.addTab(tab, "Binning")
        
        # Set initial enabled state
        self._on_bin_method_changed(self.cb_bin_method.currentText())
    
    def _build_normalization_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Shared style for math formula labels
        math_style = (
            "background-color: #f5f5f0; color: #333; padding: 8px 12px;"
            "border: 1px solid #dcdcdc; border-radius: 4px;"
            "font-family: 'Cambria Math', 'Times New Roman', serif; font-size: 12pt;"
        )
        
        # Normalization Mode
        grp_norm = QGroupBox("Normalization Mode")
        norm_layout = QVBoxLayout(grp_norm)
        
        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Mode:"))
        self.cb_normalization = QComboBox()
        self.cb_normalization.addItems(["Count", "Density", "Probability", "Percentage", "Cumulative (CDF)", "Peak (Max = 1)"])
        self.cb_normalization.setCurrentText(self.cfg.get("normalization", "Count"))
        self.cb_normalization.currentTextChanged.connect(self._on_norm_mode_changed)
        mode_row.addWidget(self.cb_normalization)
        norm_layout.addLayout(mode_row)
        
        # Math formula label — updates dynamically
        self.lbl_norm_math = QLabel()
        self.lbl_norm_math.setWordWrap(True)
        self.lbl_norm_math.setStyleSheet(math_style)
        norm_layout.addWidget(self.lbl_norm_math)
        
        layout.addWidget(grp_norm)
        
        # Statistical Overlays
        grp_overlays = QGroupBox("Statistical Overlays")
        overlay_layout = QVBoxLayout(grp_overlays)
        
        self.chk_kde = QCheckBox("Show KDE (Kernel Density Estimate) curve")
        self.chk_kde.setChecked(self.cfg.get("show_kde", False))
        self.chk_kde.toggled.connect(self._on_overlay_toggled)
        overlay_layout.addWidget(self.chk_kde)
        
        self.lbl_kde_math = QLabel()
        self.lbl_kde_math.setWordWrap(True)
        self.lbl_kde_math.setStyleSheet(math_style)
        self.lbl_kde_math.setText(
            "KDE:  f\u0302(x) = (1 / n\u00B7h) \u2211 K( (x \u2212 x\u1D62) / h )\n"
            "where K is the Gaussian kernel, h is the bandwidth"
        )
        overlay_layout.addWidget(self.lbl_kde_math)
        
        # KDE sub-options widget (visible only when KDE is checked)
        self.kde_options_widget = QWidget()
        kde_form = QFormLayout(self.kde_options_widget)
        kde_form.setContentsMargins(20, 4, 0, 4)
        
        # Kernel type (informational — scipy only supports Gaussian)
        self.cb_kde_kernel = QComboBox()
        self.cb_kde_kernel.addItems(["Gaussian"])
        self.cb_kde_kernel.setToolTip("scipy.stats.gaussian_kde only supports the Gaussian kernel")
        kde_form.addRow("Kernel:", self.cb_kde_kernel)
        
        # Bandwidth method
        self.cb_kde_bw_method = QComboBox()
        self.cb_kde_bw_method.addItems(["Auto (Scott)", "Auto (Silverman)", "Manual"])
        self.cb_kde_bw_method.setCurrentText(self.cfg.get("kde_bw_method", "Auto (Scott)"))
        self.cb_kde_bw_method.currentTextChanged.connect(self._on_kde_bw_changed)
        kde_form.addRow("Bandwidth:", self.cb_kde_bw_method)
        
        # Manual bandwidth value
        self.spin_kde_bw_value = QDoubleSpinBox()
        self.spin_kde_bw_value.setRange(0.001, 1e6)
        self.spin_kde_bw_value.setDecimals(4)
        self.spin_kde_bw_value.setSingleStep(0.01)
        self.spin_kde_bw_value.setValue(self.cfg.get("kde_bw_value", 0.5))
        self.spin_kde_bw_value.setEnabled(self.cfg.get("kde_bw_method") == "Manual")
        _spin_disabled_style = """
            QDoubleSpinBox:disabled { background-color: #e8e8e8; color: #aaaaaa; }
        """
        self.spin_kde_bw_value.setStyleSheet(_spin_disabled_style)
        kde_form.addRow("BW Value:", self.spin_kde_bw_value)
        
        # Bandwidth adjust (multiplier on auto bandwidth)
        bw_adj_widget = QWidget()
        bw_adj_layout = QHBoxLayout(bw_adj_widget)
        bw_adj_layout.setContentsMargins(0, 0, 0, 0)
        self.slider_kde_adjust = QSlider(Qt.Orientation.Horizontal)
        self.slider_kde_adjust.setRange(10, 500)  # 0.1x to 5.0x
        adjust_val = self.cfg.get("kde_bw_adjust", 1.0)
        self.slider_kde_adjust.setValue(int(adjust_val * 100))
        self.lbl_kde_adjust_val = QLabel(f"{adjust_val:.2f}")
        self.slider_kde_adjust.valueChanged.connect(
            lambda v: self.lbl_kde_adjust_val.setText(f"{v/100:.2f}")
        )
        bw_adj_layout.addWidget(self.slider_kde_adjust)
        bw_adj_layout.addWidget(self.lbl_kde_adjust_val)
        kde_form.addRow("BW Adjust:", bw_adj_widget)
        
        overlay_layout.addWidget(self.kde_options_widget)
        
        self.chk_mean = QCheckBox("Show Mean line")
        self.chk_mean.setChecked(self.cfg.get("show_mean_line", False))
        self.chk_mean.toggled.connect(self._on_overlay_toggled)
        overlay_layout.addWidget(self.chk_mean)
        
        self.lbl_mean_math = QLabel()
        self.lbl_mean_math.setWordWrap(True)
        self.lbl_mean_math.setStyleSheet(math_style)
        self.lbl_mean_math.setText(
            "Mean:  \u03BC = (1/n) \u2211 x\u1D62"
        )
        overlay_layout.addWidget(self.lbl_mean_math)
        
        self.chk_median = QCheckBox("Show Median line")
        self.chk_median.setChecked(self.cfg.get("show_median_line", False))
        self.chk_median.toggled.connect(self._on_overlay_toggled)
        overlay_layout.addWidget(self.chk_median)
        
        self.lbl_median_math = QLabel()
        self.lbl_median_math.setWordWrap(True)
        self.lbl_median_math.setStyleSheet(math_style)
        self.lbl_median_math.setText(
            "Median:  M = x\u208D\u208D\u2099\u208A\u2081\u208E\u2082\u208E   (middle value when sorted)"
        )
        overlay_layout.addWidget(self.lbl_median_math)
        
        layout.addWidget(grp_overlays)
        layout.addStretch()
        
        self.tabs.addTab(tab, "Normalization & Overlays")
        
        # Set initial state
        self._on_norm_mode_changed(self.cb_normalization.currentText())
        self._on_overlay_toggled()
    
    def _on_norm_mode_changed(self, mode):
        """Update the math formula display for the selected normalization mode."""
        formulas = {
            "Count":
                "y = n\u1D62\n"
                "where n\u1D62 is the number of data points in bin i",
            "Density":
                "y = n\u1D62 / (N \u00B7 \u0394x)\n"
                "where N = total points, \u0394x = bin width\n"
                "Area under the histogram integrates to 1",
            "Probability":
                "y = n\u1D62 / N\n"
                "where N = total points\n"
                "Bar heights sum to 1 (relative frequency)",
            "Percentage":
                "y = (n\u1D62 / N) \u00D7 100\n"
                "Identical to Probability but in percent\n"
                "Bar heights sum to 100",
            "Cumulative (CDF)":
                "y = \u2211\u2C7C\u2264\u1D62 n\u2C7C / N\n"
                "Running sum of relative frequencies\n"
                "Monotonically increases from 0 to 1",
            "Peak (Max = 1)":
                "y = n\u1D62 / max(n)\n"
                "Tallest bar is scaled to 1.0\n"
                "Useful for comparing relative spread of distributions",
        }
        self.lbl_norm_math.setText(formulas.get(mode, ""))
    
    def _on_overlay_toggled(self, _=None):
        """Show/hide math labels and KDE options based on overlay checkbox state."""
        kde_on = self.chk_kde.isChecked()
        self.lbl_kde_math.setVisible(kde_on)
        self.kde_options_widget.setVisible(kde_on)
        self.lbl_mean_math.setVisible(self.chk_mean.isChecked())
        self.lbl_median_math.setVisible(self.chk_median.isChecked())
    
    def _on_kde_bw_changed(self, text):
        self.spin_kde_bw_value.setEnabled(text == "Manual")
    
    def _build_visual_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        _btn_color_style = "border: 1px solid #aaa; border-radius: 0px; min-height: 22px;"
        
        # Histogram Style
        grp_style = QGroupBox("Histogram Style")
        form = QFormLayout(grp_style)
        
        self.cb_hist_type = QComboBox()
        self.cb_hist_type.addItems(["bar", "step", "stepfilled"])
        self.cb_hist_type.setCurrentText(self.cfg.get("hist_type", "bar"))
        form.addRow("Type:", self.cb_hist_type)
        
        # Alpha slider
        alpha_widget = QWidget()
        alpha_layout = QHBoxLayout(alpha_widget)
        alpha_layout.setContentsMargins(0, 0, 0, 0)
        self.slider_alpha = QSlider(Qt.Orientation.Horizontal)
        self.slider_alpha.setRange(0, 100)
        self.slider_alpha.setValue(int(self.cfg.get("alpha", 0.7) * 100))
        self.lbl_alpha_val = QLabel(f"{self.cfg.get('alpha', 0.7):.2f}")
        self.slider_alpha.valueChanged.connect(lambda v: self.lbl_alpha_val.setText(f"{v/100:.2f}"))
        alpha_layout.addWidget(self.slider_alpha)
        alpha_layout.addWidget(self.lbl_alpha_val)
        form.addRow("Transparency:", alpha_widget)
        
        self.cb_orientation = QComboBox()
        self.cb_orientation.addItems(["Vertical", "Horizontal"])
        self.cb_orientation.setCurrentText(self.cfg.get("orientation", "Vertical"))
        form.addRow("Orientation:", self.cb_orientation)
        
        layout.addWidget(grp_style)
        
        # Colors
        grp_colors = QGroupBox("Colors")
        color_form = QFormLayout(grp_colors)
        
        # Bar fill color
        bar_color_row = QHBoxLayout()
        self.chk_bar_color = QCheckBox("Custom")
        bar_c = self.cfg.get("bar_color")
        self.chk_bar_color.setChecked(bar_c is not None)
        self.chk_bar_color.toggled.connect(self._on_bar_color_toggled)
        bar_color_row.addWidget(self.chk_bar_color)
        
        self.btn_bar_color = QPushButton()
        self._bar_color = bar_c if bar_c else "#4a90d9"
        self.btn_bar_color.setStyleSheet(f"background-color: {self._bar_color}; {_btn_color_style}")
        self.btn_bar_color.clicked.connect(self._pick_bar_color)
        self.btn_bar_color.setEnabled(bar_c is not None)
        bar_color_row.addWidget(self.btn_bar_color)
        
        lbl_hint = QLabel("(unchecked = use mapping color)")
        lbl_hint.setStyleSheet("color: #999; font-size: 9pt;")
        bar_color_row.addWidget(lbl_hint)
        bar_color_row.addStretch()
        color_form.addRow("Bar Fill:", bar_color_row)
        
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
        
        layout.addWidget(grp_colors)
        
        # Weighted Histogram
        grp_weight = QGroupBox("Weighted Histogram")
        weight_form = QFormLayout(grp_weight)
        
        self.chk_weights = QCheckBox("Enable weighted histogram")
        self.chk_weights.setChecked(self.cfg.get("use_weights", False))
        self.chk_weights.toggled.connect(self._on_weights_toggled)
        weight_form.addRow(self.chk_weights)
        
        self.cb_weight_var = QComboBox()
        # Populate with available variables
        for j, v in enumerate(self.parent_window.var_names):
            self.cb_weight_var.addItem(f"{j+1}: {v}", j)
        w_idx = self.cfg.get("weight_var_idx")
        if w_idx is not None and w_idx < self.cb_weight_var.count():
            self.cb_weight_var.setCurrentIndex(w_idx)
        self.cb_weight_var.setEnabled(self.cfg.get("use_weights", False))
        weight_form.addRow("Weight Variable:", self.cb_weight_var)
        
        layout.addWidget(grp_weight)
        layout.addStretch()
        
        self.tabs.addTab(tab, "Visual Style")
    
    def _on_bin_method_changed(self, text):
        self.spin_bin_count.setEnabled(text == "Manual (Count)")
        self.spin_bin_width.setEnabled(text == "Manual (Width)")
        
        formulas = {
            "Auto (Sturges)":
                "k = \u2308log\u2082(n)\u2309 + 1\n"
                "Simple, works best for roughly normal data",
            "Auto (Scott)":
                "h = 3.49 \u00B7 \u03C3 \u00B7 n\u207B\u00B9\u2033\u00B3\n"
                "Optimal for normal distributions\n"
                "\u03C3 = standard deviation, h = bin width",
            "Auto (Freedman-Diaconis)":
                "h = 2 \u00B7 IQR \u00B7 n\u207B\u00B9\u2033\u00B3\n"
                "Robust to outliers, uses interquartile range\n"
                "IQR = Q\u2083 \u2212 Q\u2081",
            "Auto (sqrt)":
                "k = \u2308\u221An\u2309\n"
                "Square root of the number of data points",
            "Manual (Count)":
                "User specifies the exact number of bins k\n"
                "Bin edges are evenly spaced from min to max",
            "Manual (Width)":
                "Edges: x\u2080, x\u2080 + w, x\u2080 + 2w, \u2026\n"
                "User specifies the fixed bin width w\n"
                "Number of bins adapts to the data range",
            "Integer":
                "Edges at i \u2212 0.5 for each integer i\n"
                "Each integer value is centered in its bin\n"
                "Ideal for discrete / count data",
        }
        self.lbl_bin_math.setText(formulas.get(text, ""))
    
    def _on_weights_toggled(self, checked):
        self.cb_weight_var.setEnabled(checked)
    
    def _on_bar_color_toggled(self, checked):
        self.btn_bar_color.setEnabled(checked)
    
    def _pick_bar_color(self):
        from PyQt6.QtGui import QColor
        color = QColorDialog.getColor(QColor(self._bar_color), self, "Select Bar Fill Color")
        if color.isValid():
            self._bar_color = color.name()
            self.btn_bar_color.setStyleSheet(
                f"background-color: {color.name()}; border: 1px solid #aaa; border-radius: 0px; min-height: 22px;"
            )
    
    def _pick_edge_color(self):
        from PyQt6.QtGui import QColor
        color = QColorDialog.getColor(QColor(self._edge_color), self, "Select Edge Color")
        if color.isValid():
            self._edge_color = color.name()
            self.btn_edge_color.setStyleSheet(
                f"background-color: {color.name()}; border: 1px solid #aaa; border-radius: 0px; min-height: 22px;"
            )
    
    def _collect_cfg(self):
        """Read all widget values back into a config dict."""
        cfg = {}
        # Binning
        cfg["bin_method"] = self.cb_bin_method.currentText()
        cfg["bin_count"] = self.spin_bin_count.value()
        cfg["bin_width"] = self.spin_bin_width.value()
        try:
            cfg["bin_min"] = float(self.le_bin_min.text()) if self.le_bin_min.text().strip() else None
        except ValueError:
            cfg["bin_min"] = None
        try:
            cfg["bin_max"] = float(self.le_bin_max.text()) if self.le_bin_max.text().strip() else None
        except ValueError:
            cfg["bin_max"] = None
        
        # Normalization
        cfg["normalization"] = self.cb_normalization.currentText()
        
        # Overlays
        cfg["show_kde"] = self.chk_kde.isChecked()
        cfg["kde_bw_method"] = self.cb_kde_bw_method.currentText()
        cfg["kde_bw_value"] = self.spin_kde_bw_value.value()
        cfg["kde_bw_adjust"] = self.slider_kde_adjust.value() / 100.0
        cfg["show_mean_line"] = self.chk_mean.isChecked()
        cfg["show_median_line"] = self.chk_median.isChecked()
        
        # Visual
        cfg["hist_type"] = self.cb_hist_type.currentText()
        cfg["alpha"] = self.slider_alpha.value() / 100.0
        cfg["orientation"] = self.cb_orientation.currentText()
        cfg["bar_color"] = self._bar_color if self.chk_bar_color.isChecked() else None
        cfg["edge_color"] = self._edge_color
        cfg["edge_width"] = self.spin_edge_width.value()
        
        # Weights
        cfg["use_weights"] = self.chk_weights.isChecked()
        cfg["weight_var_idx"] = self.cb_weight_var.currentData() if self.chk_weights.isChecked() else None
        
        return cfg
    
    def apply_changes(self):
        self.parent_window.histogram_cfg = self._collect_cfg()
        # Apply per-mapping hist_var_idx from the data selection table
        self.parent_window.maps = copy.deepcopy(self.maps)
        self.parent_window.update_plot()
    
    def accept_changes(self):
        self.apply_changes()
        self.close()
