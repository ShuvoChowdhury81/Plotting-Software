import sys
import pickle
import numpy as np
import copy
from scipy import interpolate
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['Helvetica', 'Arial', 'DejaVu Sans', 'sans-serif']
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QComboBox, 
                             QColorDialog, QFileDialog, QGroupBox, QSpinBox,
                             QFormLayout, QMenuBar, QMenu, QToolBar, QDockWidget,
                             QTabWidget, QStatusBar, QSpacerItem, QSizePolicy,
                             QDialog, QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox,
                             QRadioButton, QButtonGroup, QDoubleSpinBox, QLineEdit, QMessageBox)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction, QIcon, QColor, QFont


from ui.dialogs.mapping_style import MappingStyleDialog
from ui.dialogs.legend_style import LegendDialog
from ui.dialogs.axis_details import AxisDetailsDialog
from ui.dialogs.frame_size import FrameSizePositionDialog
from ui.dialogs.append_data import AppendDataDialog
from ui.dialogs.data_manager import DataManagerDialog

class WorkspaceWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #4a4a4a;")
        self.canvas = None
        self.aspect_ratio = None # None means stretch to fill

    def set_canvas(self, canvas):
        self.canvas = canvas
        self.canvas.setParent(self)
        self.canvas.show()
        self.update_geometry()

    def set_aspect_ratio(self, ratio):
        self.aspect_ratio = ratio
        self.update_geometry()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_geometry()

    def update_geometry(self):
        if not self.canvas:
            return
            
        w = self.width() - 40 # 20px padding
        h = self.height() - 40
        
        if w < 10 or h < 10:
            return

        if self.aspect_ratio is None:
            self.canvas.setGeometry(20, 20, w, h)
        else:
            if w / h > self.aspect_ratio:
                # too wide, use full height
                cv_h = h
                cv_w = int(h * self.aspect_ratio)
            else:
                # too tall, use full width
                cv_w = w
                cv_h = int(w / self.aspect_ratio)
                
            x = 20 + (w - cv_w) // 2
            y = 20 + (h - cv_h) // 2
            
            self.canvas.setGeometry(x, y, cv_w, cv_h)

class FigaroApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_pkg_file = None
        self.update_window_title()
        self.setGeometry(100, 100, 1200, 800)
        # --- Theme Styling ---
        # Generate a white checkmark image for checkbox styling at startup
        import os, tempfile
        from PyQt6.QtGui import QPixmap, QPainter, QPen
        from PyQt6.QtCore import QPoint
        _check_pixmap = QPixmap(16, 16)
        _check_pixmap.fill(Qt.GlobalColor.transparent)
        _painter = QPainter(_check_pixmap)
        _painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        _pen = QPen(Qt.GlobalColor.white, 2.2)
        _pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        _pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        _painter.setPen(_pen)
        _painter.drawLine(QPoint(3, 8), QPoint(6, 12))
        _painter.drawLine(QPoint(6, 12), QPoint(13, 3))
        _painter.end()
        _check_img_path = os.path.join(tempfile.gettempdir(), "_qt_check_white.png")
        _check_pixmap.save(_check_img_path, "PNG")
        _check_img = _check_img_path.replace("\\", "/")
        
        stylesheet = f"""
            /* General Application Background */
            QMainWindow, QDialog {{ background-color: #f8fafc; }}

            /* Font definitions for consistency across widgets */
            QWidget {{
                font-family: "Segoe UI", "Open Sans", "Helvetica Neue", Arial, sans-serif;
                font-size: 13px;
                color: #334155;
            }}

            /* Styling the Menu Bar */
            QMenuBar {{
                background-color: #ffffff;
                border-bottom: 1px solid #e2e8f0;
            }}
            QMenuBar::item {{
                padding: 6px 10px;
                background: transparent;
            }}
            QMenuBar::item:selected {{
                background-color: #f1f5f9;
                color: #0f172a;
                border-radius: 4px;
            }}

            /* ToolBar styling */
            QToolBar {{
                background-color: #ffffff;
                border-bottom: 1px solid #e2e8f0;
                padding: 4px;
                spacing: 8px;
            }}
            QToolBar QPushButton {{
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: 600;
                color: #475569;
            }}
            QToolBar QPushButton:hover {{
                background-color: #f1f5f9;
                border: 1px solid #cbd5e1;
                color: #0f172a;
            }}
            QToolBar QPushButton:pressed {{
                background-color: #e2e8f0;
            }}

            /* QDockWidget (Sidebar) */
            QDockWidget {{
                color: #334155;
                font-weight: 600;
                border: 1px solid #e2e8f0;
            }}
            QDockWidget::title {{
                text-align: left;
                background: #f1f5f9;
                padding: 8px 12px;
                font-weight: 600;
                color: #0f172a;
                border-bottom: 1px solid #e2e8f0;
            }}

            /* Fixes for dark/blue unreadable dialogs (ComboBox drop-downs, right click menus, file dialogs) */
            QListView, QTreeView, QTableView {{
                background-color: #ffffff;
                color: #000000;
                alternate-background-color: #f8fafc;
            }}
            QListView::item:selected, QTreeView::item:selected {{
                background-color: #bfdbfe;
                color: #000000;
            }}
            QMenu {{
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #cbd5e1;
            }}
            QMenu::item:selected {{
                background-color: #bfdbfe;
                color: #000000;
            }}
            QMessageBox {{
                background-color: #ffffff;
                color: #000000;
            }}

            /* GroupBox and Forms */
            QGroupBox {{
                font-weight: 600;
                color: #0f172a;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                margin-top: 16px;
                padding-top: 16px;
                background-color: #ffffff;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 6px;
                color: #1d4ed8;
            }}

            /* Generic Push Buttons inside dialogs/docks */
            QPushButton {{
                background-color: #ffffff;
                color: #334155;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: #f8fafc;
                border: 1px solid #94a3b8;
                color: #0f172a;
            }}
            QPushButton:pressed {{
                background-color: #e2e8f0;
            }}
            QPushButton:checked {{
                background-color: #1d4ed8;
                border: 1px solid #1e3a8a;
                color: #ffffff;
            }}

            /* LineEdits and SpinBoxes */
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                padding: 5px;
                background-color: #ffffff;
                color: #334155;
                selection-background-color: #bfdbfe;
            }}
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
                border: 1px solid #3b82f6;
            }}
            QComboBox::drop-down {{
                border-left: 1px solid #cbd5e1;
                width: 24px;
            }}

            /* Tab Widgets */
            QTabWidget::pane {{
                border: 1px solid #cbd5e1;
                background-color: #ffffff;
                border-radius: 6px;
                border-top-left-radius: 0;
            }}
            QTabBar::tab {{
                background-color: #f1f5f9;
                border: 1px solid #cbd5e1;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 8px 16px;
                margin-right: 2px;
                color: #64748b;
            }}
            QTabBar::tab:selected {{
                background-color: #ffffff;
                font-weight: 600;
                color: #1d4ed8;
            }}
            QTabBar::tab:hover:!selected {{
                background-color: #e2e8f0;
                color: #334155;
            }}

            /* Table Widget */
            QTableWidget {{
                background-color: #ffffff;
                alternate-background-color: #f8fafc;
                gridline-color: #e2e8f0;
                selection-background-color: #eff6ff;
                selection-color: #1d4ed8;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
            }}
            QHeaderView::section {{
                background-color: #f1f5f9;
                color: #334155;
                font-weight: 600;
                padding: 8px;
                border: 1px solid #e2e8f0;
                border-top: none;
                border-left: none;
            }}

            /* Status Bar */
            QStatusBar {{
                background-color: #f1f5f9;
                color: #475569;
                border-top: 1px solid #cbd5e1;
            }}

            /* Radio Buttons */
            QRadioButton {{
                color: #334155;
                font-weight: 500;
                spacing: 6px;
            }}
            QCheckBox::indicator {{
                width: 14px;
                height: 14px;
                border: 2px solid #94a3b8;
                border-radius: 3px;
                background-color: #ffffff;
            }}
            QCheckBox::indicator:hover {{
                border: 2px solid #3b82f6;
            }}
            QCheckBox::indicator:checked {{
                background-color: #2563eb;
                border: 2px solid #2563eb;
                border-radius: 3px;
                image: url({_check_img});
            }}
            QRadioButton::indicator {{
                width: 16px;
                height: 16px;
                background-color: #ffffff;
                border-radius: 8px; /* Circular */
                border: 1px solid #cbd5e1;
            }}
            QRadioButton::indicator:checked {{
                background-color: #424242;
                border: 4px solid #ffffff;
                outline: 2px solid #424242;
            }}
        """
        self.setStyleSheet(stylesheet)

        # --- Data Structure ---
        self.data_vars = [] # List of numpy arrays representing columns
        self.var_names = [] # List of strings "V1", "V2"
        self.maps = []      # List of map dict mappings
        self.datasets = []  # List of dictionaries tracking file data sources
        self.leg = None     # Reference to the matplotlib legend
        
        self.legend_cfg = {
            "show_line_legend": True,
            "show_mapping_names": True,
            "font": "STIXGeneral",
            "size": 10,
            "bold": False,
            "italic": False,
            "text_color": "#000000",
            "pos_x": 95,
            "pos_y": 80,
            "line_spacing": 1.2,
            "box_type": "Outline",
            "box_line_thickness": "0.1",
            "box_color": "#000000",
            "fill_color": "#ffffff",
            "margin": 10
        }
        
        self.axis_cfg = {
            "nice_fit": False,
            "X1_show": True,
            "X1_title_text": "X Axis",
            "X1_min": None,
            "X1_max": None,
            "X1_title_offset": 6.0,
            "X1_log": False,
            "X1_reverse": False,
            "X1_line_show_grid_border": True,
            "Y1_show": True,
            "Y1_title_text": "Y Axis",
            "Y1_min": None,
            "Y1_max": None,
            "Y1_title_offset": 10.0,
            "Y1_log": False,
            "Y1_reverse": False,
            "Y1_line_show_grid_border": True
        }
        
        self.frame_cfg = {
            "paper_size": "Letter (8.5 x 11 in)",
            "orientation": "Landscape",
            "width": 6.0,
            "height": 6.0,
            "pos_x": 0.5,
            "pos_y": 0.5,
            "square_aspect": True,
            "show_border": False
        }
        
        # --- UI Setup ---
        self.setup_menu_bar()
        self.setup_toolbar()
        self.setup_central_workspace()
        self.setup_dockable_sidebar()
        
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Ready. Load a data file to begin.")
        
        self.update_plot()
        
    def setup_menu_bar(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        
        new_action = QAction("New Plot...", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.create_new_plot)
        file_menu.addAction(new_action)
        
        file_menu.addSeparator()
        
        load_action = QAction("Load Data...", self)
        load_action.setShortcut("Ctrl+O")
        load_action.triggered.connect(self.load_data)
        file_menu.addAction(load_action)
        
        save_action = QAction("Save Plot As Image...", self)
        save_action.triggered.connect(self.save_plot)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        save_pkg_action = QAction("Save Plot Package...", self)
        save_pkg_action.setShortcut("Ctrl+S")
        save_pkg_action.triggered.connect(self.save_plot_package)
        file_menu.addAction(save_pkg_action)
        
        open_pkg_action = QAction("Open Plot Package...", self)
        open_pkg_action.triggered.connect(self.open_plot_package)
        file_menu.addAction(open_pkg_action)
        
        file_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        plot_menu = menubar.addMenu("Plot")
        mapping_action = QAction("Mapping Style...", self)
        mapping_action.triggered.connect(self.open_mapping_style)
        plot_menu.addAction(mapping_action)

        data_menu = menubar.addMenu("Data")
        spreadsheet_action = QAction("Data Set Manager...", self)
        spreadsheet_action.triggered.connect(self.open_data_table)
        data_menu.addAction(spreadsheet_action)

        frame_menu = menubar.addMenu("Frame")
        frame_action = QAction("Frame Size & Position...", self)
        frame_action.triggered.connect(self.open_frame_size)
        frame_menu.addAction(frame_action)

    def setup_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(20, 20))
        toolbar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)
        
        btn_load = QPushButton("📂 Load Data")
        btn_load.setFlat(True)
        btn_load.clicked.connect(self.load_data)
        toolbar.addWidget(btn_load)
        
        # Quick access to Mapping style
        btn_map = QPushButton("🗺️ Mapping Style")
        btn_map.setStyleSheet("font-weight: bold; color: #d62728;")
        btn_map.setFlat(True)
        btn_map.clicked.connect(self.open_mapping_style)
        toolbar.addWidget(btn_map)
        
        btn_legend = QPushButton("🏷️ Legend")
        btn_legend.setFlat(True)
        btn_legend.clicked.connect(self.open_legend_style)
        toolbar.addWidget(btn_legend)
        
        btn_axis = QPushButton("📏 Axis Details")
        btn_axis.setFlat(True)
        btn_axis.clicked.connect(self.open_axis_details)
        toolbar.addWidget(btn_axis)
        
        btn_frame = QPushButton("🖼️ Frame Size")
        btn_frame.setFlat(True)
        btn_frame.clicked.connect(self.open_frame_size)
        toolbar.addWidget(btn_frame)
        
        btn_save = QPushButton("💾 Save Plot")
        btn_save.setFlat(True)
        btn_save.clicked.connect(self.save_plot)
        toolbar.addWidget(btn_save)
        
        toolbar.addSeparator()
        
        self.btn_zoom = QPushButton("🔍 Zoom/Pan")
        self.btn_zoom.setFlat(True)
        self.btn_zoom.setCheckable(True)
        self.btn_zoom.clicked.connect(self.toggle_zoom_pan)
        toolbar.addWidget(self.btn_zoom)

    def setup_central_workspace(self):
        self.workspace = WorkspaceWidget(self)
        
        # White "paper" figure
        self.figure = Figure(dpi=100)
        self.figure.patch.set_facecolor('white') # Make the entire figure background white
        self.canvas = FigureCanvas(self.figure)
        
        # Add a subtle border to the paper canvas to distinguish it from the grey background
        self.canvas.setStyleSheet("border: 1px solid #707070; background-color: white;")
        
        self.workspace.set_canvas(self.canvas)
        
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor('white') # the plot area inside the bounding box is white
        
        self.mpl_toolbar = NavigationToolbar(self.canvas, self)
        self.mpl_toolbar.hide()
        
        self.canvas.mpl_connect('scroll_event', self.on_scroll_zoom)
        self.canvas.mpl_connect('button_press_event', self.on_mouse_press)
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        self.canvas.mpl_connect('button_release_event', self.on_mouse_release)
        
        self.panning = False
        self.pan_start_x = None
        self.pan_start_y = None
        
        self.setCentralWidget(self.workspace)

    def setup_dockable_sidebar(self):
        dock = QDockWidget("Plot", self)
        dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetFloatable | QDockWidget.DockWidgetFeature.DockWidgetMovable)
        
        dock_contents = QWidget()
        dock_contents.setStyleSheet("background-color: white;")
        layout = QVBoxLayout(dock_contents)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Plot type dropdown
        self.cb_plot_type = QComboBox()
        self.cb_plot_type.addItems(["XY Line", "2D Coordinates", "3D Coordinates", "Histogram"])
        self.cb_plot_type.setCurrentText("XY Line")
        layout.addWidget(self.cb_plot_type)
        
        # Show mapping layers label
        lbl_layers = QLabel("Show mapping layers")
        lbl_layers.setStyleSheet("color: #333; font-weight: 500;")
        layout.addWidget(lbl_layers)
        
        # Mapping layer checkboxes
        layers_vbox = QVBoxLayout()
        layers_vbox.setContentsMargins(10, 0, 0, 0)
        layers_vbox.setSpacing(4)
        
        self.chk_layer_lines = QCheckBox("Lines")
        self.chk_layer_lines.setChecked(True)
        self.chk_layer_lines.toggled.connect(self._toggle_all_lines)
        layers_vbox.addWidget(self.chk_layer_lines)
        
        self.chk_layer_symbols = QCheckBox("Symbols")
        self.chk_layer_symbols.setChecked(False)
        self.chk_layer_symbols.toggled.connect(self._toggle_all_symbols)
        layers_vbox.addWidget(self.chk_layer_symbols)
        
        self.chk_layer_bars = QCheckBox("Bars")
        self.chk_layer_bars.setChecked(False)
        layers_vbox.addWidget(self.chk_layer_bars)
        
        self.chk_layer_errorbars = QCheckBox("Error bars")
        self.chk_layer_errorbars.setChecked(False)
        self.chk_layer_errorbars.toggled.connect(self._toggle_all_errorbars)
        layers_vbox.addWidget(self.chk_layer_errorbars)
        
        layout.addLayout(layers_vbox)
        
        # Mapping Style button
        btn_mapping = QPushButton("Mapping Style...")
        btn_mapping.clicked.connect(self.open_mapping_style)
        layout.addWidget(btn_mapping)
        
        # Hidden grid toggle (still referenced by update_plot grid rendering logic)
        self.btn_toggle_grid = QPushButton("Show Grid")
        self.btn_toggle_grid.setCheckable(True)
        self.btn_toggle_grid.setChecked(False)
        self.btn_toggle_grid.toggled.connect(self.update_plot)
        self.btn_toggle_grid.setVisible(False)
        layout.addWidget(self.btn_toggle_grid)
        
        layout.addStretch()
        
        dock.setWidget(dock_contents)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)

    def _toggle_all_lines(self, checked):
        for m in self.maps:
            m["show_lines"] = checked
        self.update_plot()

    def _toggle_all_symbols(self, checked):
        for m in self.maps:
            m["show_symbols"] = checked
        self.update_plot()

    def _toggle_all_errorbars(self, checked):
        for m in self.maps:
            m["show_error_bars"] = checked
        self.update_plot()

    def open_data_table(self):
        if not self.data_vars:
            self.status.showMessage("Please load data before opening Data Set Manager.")
            return
        self.data_table_dlg = DataManagerDialog(self)
        self.data_table_dlg.show()
        
    def open_mapping_style(self):
        dialog = MappingStyleDialog(self)
        dialog.exec()
        
    def open_legend_style(self):
        dialog = LegendDialog(self)
        dialog.exec()
        
    def open_axis_details(self):
        dialog = AxisDetailsDialog(self)
        dialog.exec()
        
    def open_frame_size(self):
        dialog = FrameSizePositionDialog(self)
        dialog.exec()

    def update_plot(self):
        self.ax.clear()
        
        # Iterate over mapping structures
        for m in self.maps:
            if not m.get("show", True): continue
            
            if m.get("x_var_idx", 0) >= len(self.data_vars) or m.get("y_var_idx", 0) >= len(self.data_vars):
                continue
                
            x_data = self.data_vars[m.get("x_var_idx", 0)]
            y_data = self.data_vars[m.get("y_var_idx", 0)]
            
            # Filter out NaNs and sort by X for proper fitting
            valid = ~(np.isnan(x_data) | np.isnan(y_data))
            x_clean = x_data[valid]
            y_clean = y_data[valid]
            
            if len(x_clean) < 2:
                continue
                
            sort_idx = np.argsort(x_clean)
            x_sorted = x_clean[sort_idx]
            y_sorted = y_clean[sort_idx]
            
            c_type = m.get("curve_type", "Line segment")
            
            eq_str = ""
            r2_str = ""
            
            # --- CURVE FITTING MATH ---
            try:
                if c_type == "Line segment":
                    x_plot, y_plot = x_sorted, y_sorted
                    
                elif c_type == "Linear fit":
                    coeffs = np.polyfit(x_sorted, y_sorted, 1)
                    p = np.poly1d(coeffs)
                    x_plot = np.linspace(x_sorted.min(), x_sorted.max(), 200)
                    y_plot = p(x_plot)
                    
                    y_mean = np.mean(y_sorted)
                    ss_tot = np.sum((y_sorted - y_mean)**2)
                    ss_res = np.sum((y_sorted - p(x_sorted))**2)
                    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
                    
                    def _fmt_coeff(val):
                        """Format a coefficient using LaTeX-style ×10^n for large/small numbers."""
                        s = f"{val:.4g}"
                        if 'e' in s or 'E' in s:
                            mantissa, exp = s.split('e') if 'e' in s else s.split('E')
                            exp = int(exp)
                            return f"{mantissa}×$10^{{{exp}}}$"
                        return s
                    
                    a_str = _fmt_coeff(coeffs[0])
                    b_str = _fmt_coeff(abs(coeffs[1]))
                    sign = "+" if coeffs[1] >= 0 else "−"
                    eq_str = f"y = {a_str} · x {sign} {b_str}"
                    r2_str = f"R² = {r_squared:.4f}"
                    
                elif c_type == "Polynomial fit":
                    # Let's default to a 3rd degree polynomial if no 'Curve Settings' exist yet
                    degree = 3 
                    coeffs = np.polyfit(x_sorted, y_sorted, degree)
                    p = np.poly1d(coeffs)
                    x_plot = np.linspace(x_sorted.min(), x_sorted.max(), 200)
                    y_plot = p(x_plot)
                    
                    y_mean = np.mean(y_sorted)
                    ss_tot = np.sum((y_sorted - y_mean)**2)
                    ss_res = np.sum((y_sorted - p(x_sorted))**2)
                    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
                    
                    def _fmt_coeff_poly(val):
                        s = f"{val:.4g}"
                        if 'e' in s or 'E' in s:
                            mantissa, exp = s.split('e') if 'e' in s else s.split('E')
                            exp = int(exp)
                            return f"{mantissa}×$10^{{{exp}}}$"
                        return s
                    
                    def fmt_term(c, p_pow):
                        c_str = _fmt_coeff_poly(c)
                        if p_pow == 0: return c_str
                        elif p_pow == 1: return f"{c_str} · x"
                        else: return f"{c_str} · $x^{{{p_pow}}}$"
                    eq_terms = [fmt_term(coeffs[i], degree-i) for i in range(degree+1)]
                    eq_body = " + ".join(eq_terms).replace("+ -", "− ")
                    eq_str = f"y = {eq_body}"
                    r2_str = f"R² = {r_squared:.4f}"
                    
                elif c_type == "Exponential fit":
                    # y = A * e^(B*x) => ln(y) = ln(A) + B*x
                    # Must handle strictly positive Y
                    pos_mask = y_sorted > 0
                    if not np.any(pos_mask):
                        x_plot, y_plot = x_sorted, y_sorted # fallback
                    else:
                        x_pos = x_sorted[pos_mask]
                        y_pos = y_sorted[pos_mask]
                        B, lnA = np.polyfit(x_pos, np.log(y_pos), 1,  w=np.sqrt(y_pos))
                        x_plot = np.linspace(x_sorted.min(), x_sorted.max(), 200)
                        y_plot = np.exp(lnA) * np.exp(B * x_plot)
                        
                        y_pred = np.exp(lnA) * np.exp(B * x_pos)
                        y_mean = np.mean(y_pos)
                        ss_tot = np.sum((y_pos - y_mean)**2)
                        ss_res = np.sum((y_pos - y_pred)**2)
                        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
                        
                        A_val = np.exp(lnA)
                        def _fmt_exp(val):
                            s = f"{val:.4g}"
                            if 'e' in s or 'E' in s:
                                mantissa, exp = s.split('e') if 'e' in s else s.split('E')
                                exp = int(exp)
                                return f"{mantissa}×$10^{{{exp}}}$"
                            return s
                        eq_str = f"y = {_fmt_exp(A_val)} · $e^{{{B:.4g} \\cdot x}}$"
                        r2_str = f"R² = {r_squared:.4f}"
                        
                elif c_type == "Power fit":
                    # y = A * x^B => ln(y) = ln(A) + B*ln(x)
                    # Must handle strictly positive X and Y
                    pos_mask = (x_sorted > 0) & (y_sorted > 0)
                    if not np.any(pos_mask):
                        x_plot, y_plot = x_sorted, y_sorted # fallback
                    else:
                        x_pos = x_sorted[pos_mask]
                        y_pos = y_sorted[pos_mask]
                        B, lnA = np.polyfit(np.log(x_pos), np.log(y_pos), 1)
                        x_plot = np.linspace(x_pos.min(), x_sorted.max(), 200)
                        y_plot = np.exp(lnA) * (x_plot ** B)
                        
                        y_pred = np.exp(lnA) * (x_pos ** B)
                        y_mean = np.mean(y_pos)
                        ss_tot = np.sum((y_pos - y_mean)**2)
                        ss_res = np.sum((y_pos - y_pred)**2)
                        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
                        
                        A_val = np.exp(lnA)
                        def _fmt_pow(val):
                            s = f"{val:.4g}"
                            if 'e' in s or 'E' in s:
                                mantissa, exp = s.split('e') if 'e' in s else s.split('E')
                                exp = int(exp)
                                return f"{mantissa}×$10^{{{exp}}}$"
                            return s
                        eq_str = f"y = {_fmt_pow(A_val)} · $x^{{{B:.4g}}}$"
                        r2_str = f"R² = {r_squared:.4f}"
                        
                elif c_type == "Spline":
                    # Standard Cubic Spline
                    x_unique, unique_indices = np.unique(x_sorted, return_index=True)
                    y_unique = y_sorted[unique_indices]
                    
                    if len(x_unique) > 3:
                        cs = interpolate.CubicSpline(x_unique, y_unique)
                        x_plot = np.linspace(x_unique.min(), x_unique.max(), 300)
                        y_plot = cs(x_plot)
                    else:
                        x_plot, y_plot = x_sorted, y_sorted
                        
                elif c_type == "Parametric spline":
                    # Allow non-functional curves (loops) via B-splines
                    tck, u = interpolate.splprep([x_clean, y_clean], s=0)
                    u_new = np.linspace(0, 1, 300)
                    x_plot, y_plot = interpolate.splev(u_new, tck)
                    
                elif c_type == "Akima Spline":
                    # Akima 1D interpolation minimizes overshoots
                    x_unique, unique_indices = np.unique(x_sorted, return_index=True)
                    y_unique = y_sorted[unique_indices]
                    if len(x_unique) > 3:
                        akima = interpolate.Akima1DInterpolator(x_unique, y_unique)
                        x_plot = np.linspace(x_unique.min(), x_unique.max(), 300)
                        y_plot = akima(x_plot)
                    else:
                        x_plot, y_plot = x_sorted, y_sorted
                        
                else: 
                    # Fallback for General Curve Fit, Stineman, or unimplemented
                    x_plot, y_plot = x_sorted, y_sorted
                    
            except Exception as e:
                # If math fails (e.g. singular matrix), fallback to line segments
                print(f"Curve fit failed: {e}")
                x_plot, y_plot = x_sorted, y_sorted
            
            # Plot the line/curve
            if m.get("show_lines", True):
                ls = '-'
                if m.get("line_style", "Solid") == 'Dashed': ls = '--'
                elif m.get("line_style", "Solid") == 'Dotted': ls = ':'
                
                lbl = m.get("name", "Map")
                parts = []
                if m.get("show_equation", False) and eq_str:
                    parts.append(eq_str)
                if m.get("show_r_squared", False) and r2_str:
                    parts.append(r2_str)
                if parts:
                    lbl += "\n" + ",  ".join(parts)
                    
                self.ax.plot(x_plot, y_plot, color=m.get("color", "#000000"), linestyle=ls, linewidth=m.get("line_width", 2), label=lbl)
            
            # Plot Symbols
            if m.get("show_symbols", True):
                shape_str = m.get("symbol_shape", "Square")
                marker = 's' # Square
                if shape_str == "Delta": marker = '^'
                elif shape_str == "Diamond": marker = 'D'
                elif shape_str == "Circle": marker = 'o'
                elif shape_str == "Cross": marker = 'x'
                elif shape_str == "Plus": marker = '+'
                elif shape_str == "Star": marker = '*'
                
                size_str = m.get("symbol_size", "2.50%")
                base_size = 30
                if size_str == "1.00%": base_size = 15
                elif size_str == "2.00%": base_size = 25
                elif size_str == "3.00%": base_size = 40
                elif size_str == "5.00%": base_size = 70
                
                spacing_str = m.get("symbol_spacing", "Draw all")
                step = 1
                if spacing_str == "Draw every 2nd": step = 2
                elif spacing_str == "Draw every 5th": step = 5
                elif spacing_str == "Draw every 10th": step = 10
                
                # Apply step spacing strictly to the markers
                x_sym = x_sorted[::step]
                y_sym = y_sorted[::step]
                
                edge_color = m.get("symbol_outline_color", m.get("color", "#000000"))
                fill_mode = m.get("symbol_fill_mode", "None")
                if fill_mode == "None":
                    face_color = 'none'
                elif fill_mode == "Match Base Color":
                    face_color = edge_color
                else:
                    face_color = m.get("symbol_fill_color", "#e0e0e0")
                    
                thick_str = m.get("symbol_thickness", "0.10%")
                thick = 1
                if thick_str == "0.20%": thick = 1.5
                elif thick_str == "0.40%": thick = 2
                elif thick_str == "0.80%": thick = 3
                
                # Draw the scatter plot for markers on top. Only add label if line wasn't added to avoid dupe legend
                lbl = m.get("name", "Map") if not m.get("show_lines", True) else None
                if lbl:
                    parts = []
                    if m.get("show_equation", False) and eq_str:
                        parts.append(eq_str)
                    if m.get("show_r_squared", False) and r2_str:
                        parts.append(r2_str)
                    if parts:
                        lbl += "\n" + ",  ".join(parts)
                    
                self.ax.scatter(x_sym, y_sym, marker=marker, s=base_size, 
                                edgecolors=edge_color, facecolors=face_color, 
                                linewidths=thick, zorder=5, label=lbl)
            
            # Plot Error Bars
            if m.get("show_error_bars", False) and self.chk_layer_errorbars.isChecked():
                eb_var_idx = m.get("error_bar_variable_idx", 2)
                if eb_var_idx < len(self.data_vars):
                    eb_data = self.data_vars[eb_var_idx]
                    
                    # Parse spacing
                    eb_spacing_str = m.get("error_bar_spacing", "Draw all")
                    eb_step = 1
                    if eb_spacing_str == "Draw every 2nd": eb_step = 2
                    elif eb_spacing_str == "Draw every 5th": eb_step = 5
                    elif eb_spacing_str == "Draw every 10th": eb_step = 10
                    
                    # Apply spacing to all arrays
                    x_eb = x_sorted[::eb_step]
                    y_eb = y_sorted[::eb_step]
                    # Truncate error data to match x/y length, then apply spacing
                    min_len = min(len(eb_data), len(x_sorted))
                    eb_vals = np.abs(eb_data[:min_len])[::eb_step]
                    
                    # Parse color
                    eb_color = m.get("error_bar_color", m.get("color", "#000000"))
                    
                    # Parse line thickness
                    eb_thick_str = m.get("error_bar_line_thickness", "0.10%")
                    eb_lw = 1.0
                    if eb_thick_str == "0.10%": eb_lw = 1.0
                    elif eb_thick_str == "0.20%": eb_lw = 1.5
                    elif eb_thick_str == "0.40%": eb_lw = 2.0
                    elif eb_thick_str == "0.80%": eb_lw = 3.0
                    
                    # Parse cap size from error bar size
                    eb_size_str = m.get("error_bar_size", "2.50%")
                    eb_capsize = 3.0
                    if eb_size_str == "1.00%": eb_capsize = 2.0
                    elif eb_size_str == "2.00%": eb_capsize = 3.0
                    elif eb_size_str == "2.50%": eb_capsize = 4.0
                    elif eb_size_str == "3.00%": eb_capsize = 5.0
                    elif eb_size_str == "5.00%": eb_capsize = 7.0
                    
                    # Determine error bar direction
                    eb_type = m.get("error_bar_type", "Vertical")
                    yerr_val = eb_vals if eb_type in ("Vertical", "Both") else None
                    xerr_val = eb_vals if eb_type in ("Horizontal", "Both") else None
                    
                    self.ax.errorbar(x_eb, y_eb, yerr=yerr_val, xerr=xerr_val,
                                     fmt='none', ecolor=eb_color, elinewidth=eb_lw,
                                     capsize=eb_capsize, capthick=eb_lw, zorder=4)
        
        # --- Frame Size & Aspect Ratio Implementation ---
        if self.frame_cfg.get("square_aspect", True):
            self.ax.set_box_aspect(1)
        else:
            self.ax.set_box_aspect(None) # Let it stretch dynamically
            
        show_frame_border = self.frame_cfg.get("show_border", True)
        # We will override the top/right spines if show_frame_border is False
        
        self.ax.spines['bottom'].set_linewidth(1.5)
        self.ax.spines['left'].set_linewidth(1.5)
        self.ax.spines['top'].set_linewidth(1.5)
        self.ax.spines['right'].set_linewidth(1.5)
        
        # --- Axis Configurations ---
        tight_fit = not self.axis_cfg.get("nice_fit", False)
        
        # Apply tight fit explicitly if requested before overriding
        self.ax.autoscale(enable=True, axis='both', tight=tight_fit)
        
        x_min = self.axis_cfg.get("X1_min", None)
        x_max = self.axis_cfg.get("X1_max", None)
        if x_min is not None and x_max is not None:
            self.ax.set_xlim(x_min, x_max)
        elif x_min is not None:
            self.ax.set_xlim(left=x_min)
        elif x_max is not None:
            self.ax.set_xlim(right=x_max)
            
        y_min = self.axis_cfg.get("Y1_min", None)
        y_max = self.axis_cfg.get("Y1_max", None)
        if y_min is not None and y_max is not None:
            self.ax.set_ylim(y_min, y_max)
        elif y_min is not None:
            self.ax.set_ylim(bottom=y_min)
        elif y_max is not None:
            self.ax.set_ylim(top=y_max)
            
        if self.axis_cfg["X1_log"]:
            self.ax.set_xscale('log')
        else:
            self.ax.set_xscale('linear')
            
        if self.axis_cfg["Y1_log"]:
            self.ax.set_yscale('log')
        else:
            self.ax.set_yscale('linear')
            
        # --- Apply Axis Ticks Configurations ---
        # Helper to convert "Both", "In", "Out" string to lowercase
        x_dir = self.axis_cfg.get("X1_tick_dir", "out").lower()
        y_dir = self.axis_cfg.get("Y1_tick_dir", "out").lower()
        
        # --- Label Extraction ---
        x_lbl_show = self.axis_cfg.get("X1_lbl_axis", True)
        x_lbl_size = self.axis_cfg.get("X1_lbl_fontsize", 10)
        x_lbl_color = self.axis_cfg.get("X1_lbl_color", "#000000")
        try:
            x_lbl_pad = float(self.axis_cfg.get("X1_lbl_offset", 1.0)) * 5.0
        except ValueError:
            x_lbl_pad = 5.0
            
        y_lbl_show = self.axis_cfg.get("Y1_lbl_axis", True)
        y_lbl_size = self.axis_cfg.get("Y1_lbl_fontsize", 10)
        y_lbl_color = self.axis_cfg.get("Y1_lbl_color", "#000000")
        try:
            y_lbl_pad = float(self.axis_cfg.get("Y1_lbl_offset", 1.0)) * 5.0
        except ValueError:
            y_lbl_pad = 5.0

        # X-Axis Major Ticks
        if self.axis_cfg.get("X1_show_ticks", True):
            self.ax.tick_params(axis='x', which='major', 
                                direction=x_dir,
                                length=self.axis_cfg.get("X1_tick_len", 4.0),
                                width=self.axis_cfg.get("X1_tick_width", 1.0),
                                labelsize=x_lbl_size,
                                labelcolor=x_lbl_color,
                                labelbottom=x_lbl_show,
                                pad=x_lbl_pad)
        else:
            self.ax.tick_params(axis='x', which='major', length=0, 
                                labelsize=x_lbl_size,
                                labelcolor=x_lbl_color,
                                labelbottom=x_lbl_show,
                                pad=x_lbl_pad)
            
        # Y-Axis Major Ticks
        if self.axis_cfg.get("Y1_show_ticks", True):
            self.ax.tick_params(axis='y', which='major', 
                                direction=y_dir,
                                length=self.axis_cfg.get("Y1_tick_len", 4.0),
                                width=self.axis_cfg.get("Y1_tick_width", 1.0),
                                labelsize=y_lbl_size,
                                labelcolor=y_lbl_color,
                                labelleft=y_lbl_show,
                                pad=y_lbl_pad)
        else:
            self.ax.tick_params(axis='y', which='major', length=0,
                                labelsize=y_lbl_size,
                                labelcolor=y_lbl_color,
                                labelleft=y_lbl_show,
                                pad=y_lbl_pad)
            
        # --- Axis Spacing (Major Locators & Formatters) ---
        import matplotlib.ticker as ticker
        
        # X-Axis Spacing and Formatting
        if not self.axis_cfg.get("X1_auto_spacing", True):
            base_x = self.axis_cfg.get("X1_spacing", 30.0)
            if base_x > 0:
                self.ax.xaxis.set_major_locator(ticker.MultipleLocator(base=base_x))
        else:
            self.ax.xaxis.set_major_locator(ticker.AutoLocator())
            
        x_fmt = self.axis_cfg.get("X1_lbl_format", "Normal")
        if x_fmt == "Scientific":
            x_formatter = ticker.ScalarFormatter(useMathText=True)
            x_formatter.set_scientific(True)
            x_formatter.set_powerlimits((0, 0)) # forces scientific always
            self.ax.xaxis.set_major_formatter(x_formatter)
        else:
            x_formatter = ticker.ScalarFormatter(useMathText=False)
            x_formatter.set_scientific(False)
            self.ax.xaxis.set_major_formatter(x_formatter)

        # Y-Axis Spacing and Formatting
        if not self.axis_cfg.get("Y1_auto_spacing", True):
            base_y = self.axis_cfg.get("Y1_spacing", 30.0)
            if base_y > 0:
                self.ax.yaxis.set_major_locator(ticker.MultipleLocator(base=base_y))
        else:
            self.ax.yaxis.set_major_locator(ticker.AutoLocator())
            
        y_fmt = self.axis_cfg.get("Y1_lbl_format", "Normal")
        if y_fmt == "Scientific":
            y_formatter = ticker.ScalarFormatter(useMathText=True)
            y_formatter.set_scientific(True)
            y_formatter.set_powerlimits((0, 0)) # forces scientific always
            self.ax.yaxis.set_major_formatter(y_formatter)
        else:
            y_formatter = ticker.ScalarFormatter(useMathText=False)
            y_formatter.set_scientific(False)
            self.ax.yaxis.set_major_formatter(y_formatter)
            
        # X-Axis Minor Ticks
        if self.axis_cfg.get("X1_show_minor_ticks", False):
            self.ax.minorticks_on()
            self.ax.tick_params(axis='x', which='minor',
                                direction=x_dir,
                                length=self.axis_cfg.get("X1_minor_tick_len", 2.0),
                                width=self.axis_cfg.get("X1_tick_width", 1.0) * 0.75) # minor usually slightly thinner
        else:
            self.ax.tick_params(axis='x', which='minor', length=0)
            
        # Y-Axis Minor Ticks
        if self.axis_cfg.get("Y1_show_minor_ticks", False):
            self.ax.minorticks_on()
            self.ax.tick_params(axis='y', which='minor',
                                direction=y_dir,
                                length=self.axis_cfg.get("Y1_minor_tick_len", 2.0),
                                width=self.axis_cfg.get("Y1_tick_width", 1.0) * 0.75)
        else:
            self.ax.tick_params(axis='y', which='minor', length=0)
            
        # --- Axis Titles ---
        def get_title_cfg(axis_name, default_text):
            if not self.axis_cfg.get(f"{axis_name}_show", True): 
                return "", {}, 0
                
            show = self.axis_cfg.get(f"{axis_name}_title_axis", True)
            if not show: return "", {}, 0
            
            mode = self.axis_cfg.get(f"{axis_name}_title_mode", "Use variable name")
            if mode == "Use text:":
                text = self.axis_cfg.get(f"{axis_name}_title_text", "")
            else:
                text = default_text
                
            color = self.axis_cfg.get(f"{axis_name}_title_color", "#000000")
            font = self.axis_cfg.get(f"{axis_name}_title_font", "Helvetica")
            size = self.axis_cfg.get(f"{axis_name}_title_fontsize", 12)
            weight = 'bold' if self.axis_cfg.get(f"{axis_name}_title_bold", True) else 'normal'
            style = 'italic' if self.axis_cfg.get(f"{axis_name}_title_italic", False) else 'normal'
            
            # Parse percentage offset
            try:
                offset_pct = float(self.axis_cfg.get(f"{axis_name}_title_offset", 4))
            except ValueError:
                offset_pct = 4.0
                
            props = {
                'color': color,
                'family': font,
                'fontsize': size,
                'fontweight': weight,
                'fontstyle': style
            }
            return text, props, offset_pct

        # Use the first mapping's variable names if available, else fallback
        default_x_name = "X-Axis"
        default_y_name = "Y-Axis"
        if len(self.maps) > 0:
            m = self.maps[0]
            if len(self.var_names) > max(m.get("x_var_idx", 0), m.get("y_var_idx", 0)):
                default_x_name = self.var_names[m.get("x_var_idx", 0)]
                default_y_name = self.var_names[m.get("y_var_idx", 0)]
                
        x_text, x_props, x_offset = get_title_cfg("X1", default_x_name)
        if x_text:
            self.ax.set_xlabel(x_text, **x_props)
            # 0% offset means it attaches to the axis line (y=0 in axes fraction)
            self.ax.xaxis.set_label_coords(0.5, -x_offset / 100.0)
        else:
            self.ax.set_xlabel("")

        y_text, y_props, y_offset = get_title_cfg("Y1", default_y_name)
        if y_text:
            self.ax.set_ylabel(y_text, **y_props)
            # 0% offset means it attaches to the axis line (x=0 in axes fraction)
            self.ax.yaxis.set_label_coords(-y_offset / 100.0, 0.5)
        else:
            self.ax.set_ylabel("")
            
        if self.axis_cfg["X1_reverse"]:
            if not self.ax.xaxis_inverted(): self.ax.invert_xaxis()
        else:
            if self.ax.xaxis_inverted(): self.ax.invert_xaxis()
            
        if self.axis_cfg["Y1_reverse"]:
            if not self.ax.yaxis_inverted(): self.ax.invert_yaxis()
        else:
            if self.ax.yaxis_inverted(): self.ax.invert_yaxis()
            
        x_line = self.axis_cfg.get("X1_line_show_axis", True)
        y_line = self.axis_cfg.get("Y1_line_show_axis", True)
        
        show_grid_border = self.axis_cfg.get("X1_line_show_grid_border", True) or self.axis_cfg.get("Y1_line_show_grid_border", True)
        show_frame_border = self.frame_cfg.get("show_border", False)
        
        # Display the top/right spine if either the grid border or frame border is requested
        visible_borders = show_grid_border or show_frame_border
        
        self.ax.spines['top'].set_visible(visible_borders)
        self.ax.spines['right'].set_visible(visible_borders)
        
        if not self.axis_cfg["X1_show"]:
            self.ax.get_xaxis().set_visible(False)
            self.ax.spines['bottom'].set_visible(False)
        else:
            self.ax.get_xaxis().set_visible(True)
            self.ax.spines['bottom'].set_visible(x_line or visible_borders)
            
        if not self.axis_cfg["Y1_show"]:
            self.ax.get_yaxis().set_visible(False)
            self.ax.spines['left'].set_visible(False)
        else:
            self.ax.get_yaxis().set_visible(True)
            self.ax.spines['left'].set_visible(y_line or visible_borders)
        
        # --- Advanced Label Formatting ---
        try:
            x_lbl_orient = self.axis_cfg.get("X1_lbl_orient", "At angle")
            if x_lbl_orient == "Horizontal": x_rot = 0.0
            elif x_lbl_orient == "Vertical": x_rot = 90.0
            elif x_lbl_orient == "At angle": x_rot = float(self.axis_cfg.get("X1_lbl_angle", 0))
            else: x_rot = 0.0
        except ValueError: x_rot = 0.0

        try:
            y_lbl_orient = self.axis_cfg.get("Y1_lbl_orient", "At angle")
            if y_lbl_orient == "Horizontal": y_rot = 0.0
            elif y_lbl_orient == "Vertical": y_rot = 90.0
            elif y_lbl_orient == "At angle": y_rot = float(self.axis_cfg.get("Y1_lbl_angle", 0))
            else: y_rot = 90.0
        except ValueError: y_rot = 90.0

        x_skip = self.axis_cfg.get("X1_lbl_skip", 1)
        y_skip = self.axis_cfg.get("Y1_lbl_skip", 1)

        x_font = self.axis_cfg.get("X1_lbl_font", "Helvetica")
        x_bold = "bold" if self.axis_cfg.get("X1_lbl_bold", False) else "normal"
        x_italic = "italic" if self.axis_cfg.get("X1_lbl_italic", False) else "normal"
        
        y_font = self.axis_cfg.get("Y1_lbl_font", "Helvetica")
        y_bold = "bold" if self.axis_cfg.get("Y1_lbl_bold", False) else "normal"
        y_italic = "italic" if self.axis_cfg.get("Y1_lbl_italic", False) else "normal"

        # Force drawing of ticks here to ensure get_xticklabels() picks up current dynamic ticks
        self.figure.canvas.draw()

        for i, label in enumerate(self.ax.get_xticklabels()):
            label.set_rotation(x_rot)
            label.set_fontfamily(x_font)
            label.set_fontweight(x_bold)
            label.set_fontstyle(x_italic)
            if x_skip > 1 and i % x_skip != 0:
                label.set_visible(False)
                
        for i, label in enumerate(self.ax.get_yticklabels()):
            label.set_rotation(y_rot)
            label.set_fontfamily(y_font)
            label.set_fontweight(y_bold)
            label.set_fontstyle(y_italic)
            if y_skip > 1 and i % y_skip != 0:
                label.set_visible(False)
                
        # --- Tick Direction ---
        self.ax.tick_params(direction='in', which='both')
                
        # --- Legend Rendering ---
        if self.legend_cfg.get("show_line_legend", True) and len(self.maps) > 0 and any(m.get("show", True) for m in self.maps):
            # Only use labels if show_mapping_names is checked
            handles, labels = self.ax.get_legend_handles_labels()
            if not self.legend_cfg.get("show_mapping_names", True):
                labels = [""] * len(labels)
                
            if handles:
                # Calculate matplotlib loc from percentages
                px = self.legend_cfg.get("pos_x", 95) / 100.0
                py = self.legend_cfg.get("pos_y", 80) / 100.0
                loc_tuple = (px, py)
                
                # Setup font properties
                weight = 'bold' if self.legend_cfg.get("bold", False) else 'normal'
                style = 'italic' if self.legend_cfg.get("italic", False) else 'normal'
                sz = self.legend_cfg.get("size", 10)
                family = self.legend_cfg.get("font", "sans-serif").lower()
                
                # Setup box styling
                b_type = self.legend_cfg.get("box_type", "Outline")
                frameon = (b_type != "No box")
                
                leg = self.ax.legend(handles, labels, loc='upper right', bbox_to_anchor=loc_tuple,
                                     fontsize=sz, labelcolor=self.legend_cfg.get("text_color", "#000000"),
                                     frameon=frameon, labelspacing=self.legend_cfg.get("line_spacing", 1.2),
                                     borderpad=self.legend_cfg.get("margin", 10)/10.0) 
                                     
                if frameon and leg.get_frame():
                    frame = leg.get_frame()
                    try:
                        b_thick = float(self.legend_cfg.get("box_line_thickness", "0.1")) * 10 
                    except ValueError:
                        b_thick = 1.0
                    frame.set_linewidth(b_thick)
                    
                    if b_type == "Outline":
                        frame.set_facecolor("none")
                        frame.set_edgecolor(self.legend_cfg.get("box_color", "#000000"))
                    elif b_type == "Fill":
                        frame.set_facecolor(self.legend_cfg.get("fill_color", "#ffffff"))
                        frame.set_edgecolor(self.legend_cfg.get("box_color", "#000000"))
                        
                # Attempt to apply font family and style at the text level
                for text in leg.get_texts():
                    text.set_fontfamily(family)
                    text.set_fontweight(weight)
                    text.set_fontstyle(style)
                    
                self.leg = leg
                self.leg.set_draggable(True)
        else:
            self.leg = None
            
        # --- Gridlines Rendering ---
        # Helper to parse thickness config string to float linewidth
        def parse_thick(val_str):
            try: return float(val_str) * 2.5
            except ValueError: return 0.5
                
        # Helper to parse style to matplotlib linestyle
        def parse_style(val_str):
            if val_str == "Dashed": return "--"
            elif val_str == "Dotted": return ":"
            elif val_str == "DashDot": return "-."
            return "-"
                
        # Helper to translate draw order
        def parse_order(val_str):
            return 0.5 if val_str == "First" else 10.0
                
        # X1 Axis Grid
        if self.axis_cfg.get("X1_grid_show", True):
            self.ax.grid(True, which='major', axis='x',
                         color=self.axis_cfg.get("X1_grid_color", "#000000"),
                         linestyle=parse_style(self.axis_cfg.get("X1_grid_pattern", "Solid")),
                         linewidth=parse_thick(self.axis_cfg.get("X1_grid_thick", 0.1)),
                         zorder=parse_order(self.axis_cfg.get("X1_grid_order", "First")))
        else:
            self.ax.grid(False, which='major', axis='x')
                
        if self.axis_cfg.get("X1_minor_grid_show", False):
            self.ax.grid(True, which='minor', axis='x',
                         color=self.axis_cfg.get("X1_minor_grid_color", "#000000"),
                         linestyle=parse_style(self.axis_cfg.get("X1_minor_grid_pattern", "Dotted")),
                         linewidth=parse_thick(self.axis_cfg.get("X1_minor_grid_thick", 0.1)),
                         zorder=parse_order(self.axis_cfg.get("X1_minor_grid_order", "First")))
        else:
            self.ax.grid(False, which='minor', axis='x')

        # Y1 Axis Grid
        if self.axis_cfg.get("Y1_grid_show", True):
            self.ax.grid(True, which='major', axis='y',
                         color=self.axis_cfg.get("Y1_grid_color", "#000000"),
                         linestyle=parse_style(self.axis_cfg.get("Y1_grid_pattern", "Solid")),
                         linewidth=parse_thick(self.axis_cfg.get("Y1_grid_thick", 0.1)),
                         zorder=parse_order(self.axis_cfg.get("Y1_grid_order", "First")))
        else:
            self.ax.grid(False, which='major', axis='y')
                
        if self.axis_cfg.get("Y1_minor_grid_show", False):
            self.ax.grid(True, which='minor', axis='y',
                         color=self.axis_cfg.get("Y1_minor_grid_color", "#000000"),
                         linestyle=parse_style(self.axis_cfg.get("Y1_minor_grid_pattern", "Dotted")),
                         linewidth=parse_thick(self.axis_cfg.get("Y1_minor_grid_thick", 0.1)),
                         zorder=parse_order(self.axis_cfg.get("Y1_minor_grid_order", "First")))
        else:
            self.ax.grid(False, which='minor', axis='y')
            
        # Draw text first to calculate accurate bounding boxes
        self.canvas.draw()
        
        # Apply layout adjustment based on settings
        if self.frame_cfg.get("square_aspect", True):
            # Enforce tight clipping around the plot when building a strict square
            # Instead of tight_layout which moves things organically each time, use a fixed generous 
            # margin so titles don't get shifted recursively
            self.workspace.set_aspect_ratio(1.0)
            self.figure.subplots_adjust(left=0.13, right=0.90, top=0.90, bottom=0.10)
        else:
            # Let it stretch freely based on initial subplots_adjust
            self.workspace.set_aspect_ratio(None)
            self.figure.subplots_adjust(left=0.13, right=0.95, top=0.92, bottom=0.10)

        self.canvas.draw()
        
    def save_plot(self):
        self.mpl_toolbar.save_figure()
        
    def save_plot_package(self):
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save Plot Package", "", "Plot Package Files (*.pltpkg);;All Files (*)"
        )
        if file_name:
            app_state = {
                "data_vars": self.data_vars,
                "var_names": self.var_names,
                "maps": self.maps,
                "datasets": self.datasets,
                "axis_cfg": self.axis_cfg,
                "frame_cfg": self.frame_cfg,
                "legend_cfg": self.legend_cfg
            }
            try:
                with open(file_name, 'wb') as f:
                    pickle.dump(app_state, f)
                self.current_pkg_file = file_name
                self.update_window_title()
                self.status.showMessage(f"Successfully saved plot package: {file_name}")
            except Exception as e:
                self.status.showMessage(f"Failed to save package: {e}")

    def open_plot_package(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open Plot Package", "", "Plot Package Files (*.pltpkg);;All Files (*)"
        )
        if file_name:
            try:
                with open(file_name, 'rb') as f:
                    app_state = pickle.load(f)
                
                # Restore state
                self.data_vars = app_state.get("data_vars", [])
                self.var_names = app_state.get("var_names", [])
                self.maps = app_state.get("maps", [])
                self.datasets = app_state.get("datasets", app_state.get("zones", []))
                
                # Fallback to create a default dataset for older plot packages that didn't save datasets yet
                if not self.datasets and self.data_vars:
                    self.datasets = [{"name": "Default Dataset (Legacy)", "start_idx": 0, "count": len(self.data_vars)}]
                    
                self.axis_cfg = app_state.get("axis_cfg", self.axis_cfg)
                self.frame_cfg = app_state.get("frame_cfg", {})
                self.legend_cfg = app_state.get("legend_cfg", {})
                
                self.current_pkg_file = file_name
                self.update_window_title()
                
                self.update_plot()
                self.status.showMessage(f"Successfully loaded plot package: {file_name}")
            except Exception as e:
                self.status.showMessage(f"Failed to load package: {e}")

    def update_window_title(self):
        base_title = "Figaro"
        if self.current_pkg_file:
            # Extract just the filename for cleaner display, or show full path
            import os
            display_name = os.path.basename(self.current_pkg_file)
            self.setWindowTitle(f"{base_title} - {display_name}")
        else:
            self.setWindowTitle(f"{base_title} - untitled")
        
    def toggle_zoom_pan(self):
        self.mpl_toolbar.pan()
        if self.btn_zoom.isChecked():
            self.status.showMessage("Navigation Mode: Drag to pan, Right-drag to zoom.")
        else:
            self.status.showMessage("Navigation Mode Disabled.")

    def on_scroll_zoom(self, event):
        base_scale = 1.1
        cur_xlim = self.ax.get_xlim()
        cur_ylim = self.ax.get_ylim()
        
        xdata = event.xdata
        ydata = event.ydata
        if xdata is None or ydata is None: return
            
        if event.button == 'up': scale_factor = 1 / base_scale
        elif event.button == 'down': scale_factor = base_scale
        else: scale_factor = 1
            
        new_width = (cur_xlim[1] - cur_xlim[0]) * scale_factor
        new_height = (cur_ylim[1] - cur_ylim[0]) * scale_factor
        
        relx = (cur_xlim[1] - xdata) / (cur_xlim[1] - cur_xlim[0])
        rely = (cur_ylim[1] - ydata) / (cur_ylim[1] - cur_ylim[0])
        
        self.ax.set_xlim([xdata - new_width * (1 - relx), xdata + new_width * relx])
        self.ax.set_ylim([ydata - new_height * (1 - rely), ydata + new_height * rely])
        self.canvas.draw()

    def on_mouse_press(self, event):
        if self.leg:
            contains, _ = self.leg.contains(event)
            if contains and event.button == 1:
                if event.dblclick:
                    self.open_legend_style()
                return # Do not trigger panning if interacting with legend
                
        if event.button == 1 and event.inaxes == self.ax:
            self.panning = True
            self.pan_start_x = event.xdata
            self.pan_start_y = event.ydata
            QApplication.setOverrideCursor(Qt.CursorShape.ClosedHandCursor)

    def on_mouse_move(self, event):
        if not self.panning or event.inaxes != self.ax: return
        dx = event.xdata - self.pan_start_x
        dy = event.ydata - self.pan_start_y
        cur_xlim = self.ax.get_xlim()
        cur_ylim = self.ax.get_ylim()
        self.ax.set_xlim([cur_xlim[0] - dx, cur_xlim[1] - dx])
        self.ax.set_ylim([cur_ylim[0] - dy, cur_ylim[1] - dy])
        self.canvas.draw()

    def on_mouse_release(self, event):
        if event.button == 1:
            self.panning = False
            QApplication.restoreOverrideCursor()
            
            # If the legend was dragged, save its new positional state
            if self.leg:
                try:
                    bbox = self.leg.get_window_extent()
                    ax_bbox = self.ax.transAxes.inverted().transform_bbox(bbox)
                    # The legend is anchored upper-right. So we want x1, y1 (top right) in fractional axes coords
                    self.legend_cfg["pos_x"] = round(ax_bbox.x1 * 100, 2)
                    self.legend_cfg["pos_y"] = round(ax_bbox.y1 * 100, 2)
                except BaseException:
                    pass

    def load_data(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open 2D Data File", "", "DAT Files (*.dat);;CSV Files (*.csv);;Text Files (*.txt);;All Files (*)")
        if file_name:
            # Check if data already exists and prompt user
            choice = "replace"
            if self.data_vars:
                dialog = AppendDataDialog(self)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    choice = dialog.get_choice()
                else:
                    return # User cancelled the load operation
                    
            try:
                with open(file_name, 'r') as f:
                    lines = f.readlines()
                
                parsed_data = []
                headers = []
                for line in lines:
                    line = line.strip()
                    L_lower = line.lower()
                    
                    if L_lower.startswith('variables'):
                        # Very naive parse of variables line
                        raw_vars = line.split('=')[1] if '=' in line else line
                        headers = [v.strip(' ",\'') for v in raw_vars.split(',') if v.strip(' ",\'')]
                        continue
                        
                    if not line or L_lower.startswith(('zone', 'title', 'data', '#', 'text')):
                        continue
                        
                    parts = line.split(',') if ',' in line else line.split()
                    try:
                        row = [float(p) for p in parts]
                        parsed_data.append(row)
                    except ValueError:
                        pass
                        
                if parsed_data:
                    data = np.array(parsed_data)
                    num_cols = data.shape[1]
                    new_cols = [data[:, i] for i in range(num_cols)]
                    
                    # Fill standard headers if missing
                    if len(headers) < num_cols:
                        for i in range(len(headers), num_cols):
                            headers.append(f"V{i+1}")
                            
                    import os
                    dataset_id = 1 if choice == "replace" else len(self.datasets) + 1
                    dataset_name = f"Dataset {dataset_id}: {os.path.basename(file_name)}"
                    
                    # Prefix headers with the Dataset Name to cleanly label variables across datasets!
                    new_headers = [f"Dataset {dataset_id}: {h}" for h in headers[:num_cols]]
                    
                    # Preselected dynamic color table for distinct distinct lines
                    color_palette = ["#1f77b4", "#d62728", "#2ca02c", "#ff7f0e", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"]
                    
                    if choice == "replace":
                        self.data_vars = new_cols
                        self.var_names = new_headers
                        self.datasets = [{"name": dataset_name, "start_idx": 0, "count": num_cols}]
                        
                        self.maps = [{
                            "show": True,
                            "show_lines": True,
                            "show_symbols": False,
                            "name": "Map 1",
                            "x_var_idx": 0,
                            "y_var_idx": min(1, num_cols-1),
                            "color": color_palette[0],
                            "line_style": "Solid",
                            "line_width": 2,
                            "pattern_length": "2.00%",
                            "curve_type": "Line segment",
                            "symbol_shape": "Square",
                            "symbol_size": "2.50%",
                            "symbol_spacing": "Draw all",
                            "symbol_outline_color": color_palette[0],
                            "symbol_fill_mode": "None",
                            "show_error_bars": False,
                            "error_bar_variable_idx": min(2, num_cols-1),
                            "error_bar_type": "Vertical",
                            "error_bar_spacing": "Draw all",
                            "error_bar_color": color_palette[0],
                            "error_bar_size": "2.50%",
                            "error_bar_line_thickness": "0.10%"
                        }]
                    else:
                        # Append Mode
                        # Pad the existing or new arrays to match max_length if they differ
                        offset = len(self.data_vars)
                        
                        # Add new columns to the combined dataset
                        self.data_vars.extend(new_cols)
                        
                        # Add new headers
                        for h in new_headers:
                            self.var_names.append(h)
                            
                        # Add tracking dataset
                        self.datasets.append({"name": dataset_name, "start_idx": offset, "count": num_cols})
                            
                        # Select the next color in the palette
                        c_idx = len(self.maps) % len(color_palette)
                        next_color = color_palette[c_idx]
                            
                        # Add a new map utilizing the freshly appended appended data
                        new_map = {
                            "show": True,
                            "show_lines": True,
                            "show_symbols": False,
                            "name": f"Map {len(self.maps) + 1}",
                            "x_var_idx": offset, # X is the first column of the appended data
                            "y_var_idx": min(offset + 1, len(self.data_vars) - 1),
                            "color": next_color,
                            "line_style": "Solid",
                            "line_width": 2,
                            "pattern_length": "2.00%",
                            "curve_type": "Line segment",
                            "symbol_shape": "Delta",
                            "symbol_size": "2.50%",
                            "symbol_spacing": "Draw all",
                            "symbol_outline_color": next_color,
                            "symbol_fill_mode": "None",
                            "show_error_bars": False,
                            "error_bar_variable_idx": min(offset + 2, len(self.data_vars) - 1),
                            "error_bar_type": "Vertical",
                            "error_bar_spacing": "Draw all",
                            "error_bar_color": next_color,
                            "error_bar_size": "2.50%",
                            "error_bar_line_thickness": "0.10%"
                        }
                        self.maps.append(new_map)
                    
                    self.setWindowTitle(f"Figaro - {file_name}")
                    self.update_plot()
                    self.status.showMessage(f"Successfully loaded data. Click Mapping Style to configure.")
                    
                    # Auto-open mapping style to show off the feature!
                    self.open_mapping_style()
                else:
                    self.status.showMessage("Error: No valid numeric data columns found.")
                    
            except Exception as e:
                self.status.showMessage(f"Error loading file: {str(e)}")

    def prompt_save_changes(self):
        """Prompt to save changes before discarding state. Returns True if we should proceed, False to cancel."""
        if not self.data_vars and not self.maps:
            return True # Nothing to inherently save
            
        msg = QMessageBox(self)
        msg.setWindowTitle("Unsaved Changes")
        msg.setText("Do you want to save the current plot package before proceeding?")
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setStandardButtons(QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel)
        msg.setDefaultButton(QMessageBox.StandardButton.Save)
        
        choice = msg.exec()
        if choice == QMessageBox.StandardButton.Save:
            self.save_plot_package()
            return True # Proceed after saving
        elif choice == QMessageBox.StandardButton.Cancel:
            return False
            
        return True # Proceed with Discard

    def create_new_plot(self):
        if not self.prompt_save_changes():
            return
            
        if hasattr(self, 'axis_details') and self.axis_details.isVisible():
            self.axis_details.close()
            
        # Hard reset
        self.data_vars = []
        self.var_names = []
        self.maps = []       # List of dictionaries, each describing a line mapping
        self.datasets = []   # List of dictionaries tracking file data sources
        self.current_pkg_file = None
        
        # Reset axes and frames to default baseline defined in __init__
        self.axis_cfg = {
            "X1_show": True,
            "X1_title_text": "X Axis",
            "X1_min": None,
            "X1_max": None,
            "X1_title_offset": 6.0,
            "X1_log": False,
            "X1_reverse": False,
            "X1_line_show_grid_border": True,
            "Y1_show": True,
            "Y1_title_text": "Y Axis",
            "Y1_min": None,
            "Y1_max": None,
            "Y1_title_offset": 10.0,
            "Y1_log": False,
            "Y1_reverse": False,
            "Y1_line_show_grid_border": True
        }
        
        self.frame_cfg = {
            "paper_size": "Letter (8.5 x 11 in)",
            "orientation": "Landscape",
            "width": 6.0,
            "height": 6.0,
            "pos_x": 0.5,
            "pos_y": 0.5,
            "square_aspect": True,
            "show_border": False
        }
        
        self.legend_cfg = {
            "show_line_legend": True,
            "show_mapping_names": True,
            "box_type": "Plain",
            "text_color": "#000000",
            "bg_color": "#ffffff",
            "font": "Arial",
            "fontsize": 10
        }
        
        self.update_window_title()
        self.update_plot()
        self.status.showMessage("Created a new blank plot.")

    def closeEvent(self, event):
        if self.prompt_save_changes():
            event.accept()
        else:
            event.ignore()
