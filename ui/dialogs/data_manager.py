import numpy as np
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QMessageBox, QListWidget,
                             QLabel)
from PyQt6.QtCore import Qt

class DataManagerDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Data Set Manager")
        self.resize(900, 600)
        self.parent_window = parent
        
        main_layout = QHBoxLayout(self)
        
        # Left Panel: Dataset List
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Loaded Datasets:"))
        self.dataset_list = QListWidget()
        left_layout.addWidget(self.dataset_list)
        
        # Right Panel: Spreadsheet for selected Dataset
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Dataset Spreadsheet Data:"))
        self.table = QTableWidget()
        right_layout.addWidget(self.table)
        
        # Adjust split ratio roughly 1:3
        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 3)
        
        self.populate_datasets()
        
        # Connections
        self.dataset_list.currentRowChanged.connect(self.on_dataset_selected)
        self.table.cellChanged.connect(self.on_cell_changed)
        
        # Select first dataset by default if any exist
        if self.parent_window.datasets:
            self.dataset_list.setCurrentRow(0)
            
    def populate_datasets(self):
        self.dataset_list.clear()
        for dataset in self.parent_window.datasets:
            self.dataset_list.addItem(dataset["name"])
            
    def on_dataset_selected(self, current_row):
        if current_row < 0 or current_row >= len(self.parent_window.datasets):
            self.table.setColumnCount(0)
            self.table.setRowCount(0)
            return
            
        # Temporarily block signals so population doesn't trigger cellChanged
        self.table.blockSignals(True)
        self.table.clear()
        
        dataset = self.parent_window.datasets[current_row]
        start_idx = dataset["start_idx"]
        count = dataset["count"]
        
        data_vars = self.parent_window.data_vars[start_idx:start_idx+count]
        var_names = self.parent_window.var_names[start_idx:start_idx+count]
        
        if not data_vars:
            self.table.setColumnCount(0)
            self.table.setRowCount(0)
            self.table.blockSignals(False)
            return
            
        col_count = len(data_vars)
        row_count = max(len(arr) for arr in data_vars)
        
        self.table.setColumnCount(col_count)
        self.table.setRowCount(row_count)
        self.table.setHorizontalHeaderLabels(var_names)
        
        for col_idx, arr in enumerate(data_vars):
            for row_idx, val in enumerate(arr):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row_idx, col_idx, item)
                
        if col_count < 6:
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        else:
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
            self.table.resizeColumnsToContents()
            
        self.table.blockSignals(False)

    def on_cell_changed(self, row, column):
        item = self.table.item(row, column)
        if not item: return
        
        # Determine the currently selected dataset to get absolute col index
        current_dataset_idx = self.dataset_list.currentRow()
        if current_dataset_idx < 0: return
        
        dataset = self.parent_window.datasets[current_dataset_idx]
        absolute_col = dataset["start_idx"] + column
        
        new_text = item.text()
        try:
            new_val = float(new_text)
            
            if absolute_col < len(self.parent_window.data_vars) and row < len(self.parent_window.data_vars[absolute_col]):
                self.parent_window.data_vars[absolute_col][row] = new_val
                self.parent_window.update_plot()
                
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid numeric value.")
            self.table.blockSignals(True)
            old_val = self.parent_window.data_vars[absolute_col][row]
            item.setText(str(old_val))
            self.table.blockSignals(False)
