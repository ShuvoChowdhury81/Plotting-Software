import numpy as np
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QMessageBox, QListWidget,
                             QLabel, QPushButton, QInputDialog, QApplication)
from PyQt6.QtCore import Qt


class DataManagerDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Data Set Manager")
        self.resize(900, 600)
        self.parent_window = parent
        
        outer_layout = QVBoxLayout(self)
        
        # ── Content area (left panel + right panel) ──
        content_layout = QHBoxLayout()
        
        # ── Left Panel: Dataset List ──
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Loaded Datasets:"))
        self.dataset_list = QListWidget()
        left_layout.addWidget(self.dataset_list)
        
        # Buttons below dataset list
        btn_layout = QHBoxLayout()
        
        self.btn_create = QPushButton("＋ Create New")
        self.btn_create.setToolTip("Create a new empty dataset — paste data into it with Ctrl+V")
        self.btn_create.clicked.connect(self._create_new_dataset)
        btn_layout.addWidget(self.btn_create)
        
        self.btn_delete = QPushButton("✕ Delete")
        self.btn_delete.setToolTip("Delete the selected dataset and its associated maps")
        self.btn_delete.clicked.connect(self._delete_dataset)
        btn_layout.addWidget(self.btn_delete)
        
        left_layout.addLayout(btn_layout)
        
        # ── Right Panel: Spreadsheet ──
        right_layout = QVBoxLayout()
        
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Dataset Spreadsheet Data:"))
        self.lbl_hint = QLabel("")
        self.lbl_hint.setStyleSheet("color: #6366f1; font-size: 11px; font-style: italic;")
        header_layout.addWidget(self.lbl_hint)
        header_layout.addStretch()
        right_layout.addLayout(header_layout)
        
        self.table = QTableWidget()
        right_layout.addWidget(self.table)
        
        # Split ratio ~1:3
        content_layout.addLayout(left_layout, 1)
        content_layout.addLayout(right_layout, 3)
        outer_layout.addLayout(content_layout)
        
        # ── Bottom Buttons: Apply / Ok / Close ──
        bottom_btn_layout = QHBoxLayout()
        bottom_btn_layout.addStretch()
        
        btn_apply = QPushButton("Apply")
        btn_apply.clicked.connect(self.apply_changes)
        bottom_btn_layout.addWidget(btn_apply)
        
        btn_ok = QPushButton("Ok")
        btn_ok.clicked.connect(self.accept_changes)
        btn_ok.setDefault(True)
        bottom_btn_layout.addWidget(btn_ok)
        
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.close)
        bottom_btn_layout.addWidget(btn_close)
        
        outer_layout.addLayout(bottom_btn_layout)
        
        self.populate_datasets()
        
        # Connections
        self.dataset_list.currentRowChanged.connect(self.on_dataset_selected)
        self.table.cellChanged.connect(self.on_cell_changed)
        
        # Track indices of newly created (empty placeholder) datasets
        self._new_dataset_indices = set()
        
        # Select first dataset by default if any exist
        if self.parent_window.datasets:
            self.dataset_list.setCurrentRow(0)
            
    # ─────────────────────────────────────────────────────────────
    #  Apply / Ok / Close
    # ─────────────────────────────────────────────────────────────
    def apply_changes(self):
        self.parent_window.update_plot()

    def accept_changes(self):
        self.apply_changes()
        self.close()

    # ─────────────────────────────────────────────────────────────
    #  Dataset list & table population
    # ─────────────────────────────────────────────────────────────
    def populate_datasets(self):
        self.dataset_list.clear()
        for dataset in self.parent_window.datasets:
            self.dataset_list.addItem(dataset["name"])
            
    def on_dataset_selected(self, current_row):
        if current_row < 0 or current_row >= len(self.parent_window.datasets):
            self.table.setColumnCount(0)
            self.table.setRowCount(0)
            self.lbl_hint.setText("")
            return
        
        # Contextual hint
        if current_row in self._new_dataset_indices:
            self.lbl_hint.setText("💡 Press Ctrl+V to paste data from your clipboard")
        else:
            self.lbl_hint.setText("💡 Ctrl+C to copy · Ctrl+V to paste / replace data")
            
        # Temporarily block signals so population doesn't trigger cellChanged
        self.table.blockSignals(True)
        self.table.clear()
        
        dataset = self.parent_window.datasets[current_row]
        start_idx = dataset["start_idx"]
        count = dataset["count"]
        
        data_vars = self.parent_window.data_vars[start_idx:start_idx+count]
        var_names = self.parent_window.var_names[start_idx:start_idx+count]
        
        # Check if all arrays are empty (new placeholder dataset)
        all_empty = all(len(arr) == 0 for arr in data_vars) if data_vars else True
        
        if not data_vars or all_empty:
            # Show a small empty grid for pasting
            self.table.setColumnCount(2)
            self.table.setRowCount(10)
            self.table.setHorizontalHeaderLabels(["V1", "V2"])
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
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
            if absolute_col < len(self.parent_window.data_vars) and row < len(self.parent_window.data_vars[absolute_col]):
                old_val = self.parent_window.data_vars[absolute_col][row]
                item.setText(str(old_val))
            else:
                item.setText("")
            self.table.blockSignals(False)

    # ─────────────────────────────────────────────────────────────
    #  Keyboard shortcuts  (Ctrl+C, Ctrl+V)
    # ─────────────────────────────────────────────────────────────
    def keyPressEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_V:
                self._paste_from_clipboard()
                return
            elif event.key() == Qt.Key.Key_C:
                self._copy_to_clipboard()
                return
        super().keyPressEvent(event)

    # ─────────────────────────────────────────────────────────────
    #  Create New Dataset
    # ─────────────────────────────────────────────────────────────
    def _create_new_dataset(self):
        dataset_id = len(self.parent_window.datasets) + 1
        default_name = f"Dataset {dataset_id}: Pasted Data"
        
        name, ok = QInputDialog.getText(
            self, "New Dataset", "Dataset name:", text=default_name
        )
        if not ok or not name.strip():
            return
            
        name = name.strip()
        offset = len(self.parent_window.data_vars)
        
        # Add two empty placeholder columns
        self.parent_window.data_vars.append(np.array([]))
        self.parent_window.data_vars.append(np.array([]))
        self.parent_window.var_names.append(f"Dataset {dataset_id}: V1")
        self.parent_window.var_names.append(f"Dataset {dataset_id}: V2")
        
        self.parent_window.datasets.append({
            "name": name,
            "start_idx": offset,
            "count": 2
        })
        
        new_idx = len(self.parent_window.datasets) - 1
        self._new_dataset_indices.add(new_idx)
        
        # Refresh the list and select the new dataset
        self.populate_datasets()
        self.dataset_list.setCurrentRow(new_idx)

    # ─────────────────────────────────────────────────────────────
    #  Delete Dataset
    # ─────────────────────────────────────────────────────────────
    def _delete_dataset(self):
        current_row = self.dataset_list.currentRow()
        if current_row < 0:
            return
            
        dataset = self.parent_window.datasets[current_row]
        reply = QMessageBox.question(
            self, "Delete Dataset",
            f"Are you sure you want to delete '{dataset['name']}'?\n\n"
            "This will also remove any maps that reference this dataset's variables.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
            
        start_idx = dataset["start_idx"]
        count = dataset["count"]
        
        # Remove data columns and names
        del self.parent_window.data_vars[start_idx:start_idx + count]
        del self.parent_window.var_names[start_idx:start_idx + count]
        
        # Remove maps that reference deleted variable indices
        self.parent_window.maps = [
            m for m in self.parent_window.maps
            if not (start_idx <= m["x_var_idx"] < start_idx + count
                    or start_idx <= m["y_var_idx"] < start_idx + count)
        ]
        
        # Shift variable indices in surviving maps
        for m in self.parent_window.maps:
            if m["x_var_idx"] >= start_idx + count:
                m["x_var_idx"] -= count
            if m["y_var_idx"] >= start_idx + count:
                m["y_var_idx"] -= count
            if m.get("error_bar_variable_idx", -1) >= start_idx + count:
                m["error_bar_variable_idx"] -= count
        
        # Remove dataset entry and shift subsequent start indices
        del self.parent_window.datasets[current_row]
        for ds in self.parent_window.datasets[current_row:]:
            ds["start_idx"] -= count
        
        # Update the new-dataset tracking set
        self._new_dataset_indices.discard(current_row)
        self._new_dataset_indices = {
            (i - 1 if i > current_row else i) for i in self._new_dataset_indices
        }
        
        # Refresh UI
        self.populate_datasets()
        self.parent_window.update_plot()
        
        if self.parent_window.datasets:
            self.dataset_list.setCurrentRow(
                min(current_row, len(self.parent_window.datasets) - 1)
            )

    # ─────────────────────────────────────────────────────────────
    #  Paste from clipboard  (Ctrl+V)
    # ─────────────────────────────────────────────────────────────
    def _paste_from_clipboard(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if not text or not text.strip():
            self.parent_window.status.showMessage("Clipboard is empty — nothing to paste.")
            return
        
        # ── Parse clipboard text ──
        lines = text.strip().split('\n')
        parsed_rows = []
        headers = []
        
        for i, line in enumerate(lines):
            line = line.strip('\r')
            if not line:
                continue
                
            # Detect delimiter: tab → comma → whitespace
            if '\t' in line:
                parts = line.split('\t')
            elif ',' in line:
                parts = line.split(',')
            else:
                parts = line.split()
            
            # Try parsing every cell as a number
            row = []
            all_numeric = True
            for p in parts:
                p = p.strip().strip('"').strip("'")
                try:
                    row.append(float(p))
                except ValueError:
                    all_numeric = False
                    break
            
            if all_numeric and row:
                parsed_rows.append(row)
            elif i == 0 and not all_numeric:
                # First row is likely a header row
                headers = [p.strip().strip('"').strip("'") for p in parts]
        
        if not parsed_rows:
            QMessageBox.warning(
                self, "Paste Error",
                "Could not parse any numeric data from the clipboard.\n\n"
                "Expected tab-separated, comma-separated, or space-separated numbers.\n"
                "Header rows (non-numeric first row) are detected automatically."
            )
            return
        
        # Ensure all rows have the same column count (pad shorter rows with NaN)
        max_cols = max(len(r) for r in parsed_rows)
        for r in parsed_rows:
            while len(r) < max_cols:
                r.append(float('nan'))
        
        data = np.array(parsed_rows)
        num_cols = data.shape[1]
        num_rows = data.shape[0]
        new_cols = [data[:, i] for i in range(num_cols)]
        
        # ── Determine target dataset ──
        current_dataset_idx = self.dataset_list.currentRow()
        if current_dataset_idx < 0:
            # No dataset selected — create one first
            self._create_new_dataset()
            current_dataset_idx = self.dataset_list.currentRow()
            if current_dataset_idx < 0:
                return
        
        dataset = self.parent_window.datasets[current_dataset_idx]
        dataset_id = current_dataset_idx + 1
        start_idx = dataset["start_idx"]
        old_count = dataset["count"]
        
        # Build column headers
        if not headers:
            headers = [f"V{i+1}" for i in range(num_cols)]
        while len(headers) < num_cols:
            headers.append(f"V{len(headers)+1}")
        new_headers = [f"Dataset {dataset_id}: {h}" for h in headers[:num_cols]]
        
        is_new = current_dataset_idx in self._new_dataset_indices
        
        # ── Replace the old columns with new pasted data ──
        del self.parent_window.data_vars[start_idx:start_idx + old_count]
        del self.parent_window.var_names[start_idx:start_idx + old_count]
        
        for i, col in enumerate(new_cols):
            self.parent_window.data_vars.insert(start_idx + i, col)
        for i, h in enumerate(new_headers):
            self.parent_window.var_names.insert(start_idx + i, h)
        
        dataset["count"] = num_cols
        
        # Adjust subsequent datasets' start indices
        diff = num_cols - old_count
        for ds in self.parent_window.datasets[current_dataset_idx + 1:]:
            ds["start_idx"] += diff
        
        # ── Update maps ──
        if is_new:
            # Data is now available — no map is auto-created;
            # the user can assign these variables to a map via Mapping Style.
            self._new_dataset_indices.discard(current_dataset_idx)
        else:
            # Re-pasting into an existing dataset → adjust surviving maps
            for m in self.parent_window.maps:
                if start_idx <= m["x_var_idx"] < start_idx + old_count:
                    m["x_var_idx"] = min(m["x_var_idx"], start_idx + num_cols - 1)
                elif m["x_var_idx"] >= start_idx + old_count:
                    m["x_var_idx"] += diff
                    
                if start_idx <= m["y_var_idx"] < start_idx + old_count:
                    m["y_var_idx"] = min(m["y_var_idx"], start_idx + num_cols - 1)
                elif m["y_var_idx"] >= start_idx + old_count:
                    m["y_var_idx"] += diff
                    
                ebar_idx = m.get("error_bar_variable_idx", -1)
                if start_idx <= ebar_idx < start_idx + old_count:
                    m["error_bar_variable_idx"] = min(ebar_idx, start_idx + num_cols - 1)
                elif ebar_idx >= start_idx + old_count:
                    m["error_bar_variable_idx"] = ebar_idx + diff
        
        # ── Refresh ──
        self.on_dataset_selected(current_dataset_idx)
        self.parent_window.update_plot()
        self.parent_window.status.showMessage(
            f"Pasted {num_rows} rows × {num_cols} columns into '{dataset['name']}'."
        )

    # ─────────────────────────────────────────────────────────────
    #  Copy to clipboard  (Ctrl+C)
    # ─────────────────────────────────────────────────────────────
    def _copy_to_clipboard(self):
        selection = self.table.selectedRanges()
        if not selection:
            return
            
        rows = set()
        cols = set()
        for r in selection:
            for row in range(r.topRow(), r.bottomRow() + 1):
                rows.add(row)
            for col in range(r.leftColumn(), r.rightColumn() + 1):
                cols.add(col)
        
        rows = sorted(rows)
        cols = sorted(cols)
        
        lines = []
        for row in rows:
            cells = []
            for col in cols:
                item = self.table.item(row, col)
                cells.append(item.text() if item else "")
            lines.append("\t".join(cells))
            
        text = "\n".join(lines)
        QApplication.clipboard().setText(text)
        self.parent_window.status.showMessage(
            f"Copied {len(rows)} rows × {len(cols)} columns to clipboard."
        )

    # ─────────────────────────────────────────────────────────────
    #  Cleanup empty placeholder datasets on dialog close
    # ─────────────────────────────────────────────────────────────
    def closeEvent(self, event):
        # Remove datasets that were created but never had data pasted
        indices_to_remove = sorted(self._new_dataset_indices, reverse=True)
        for idx in indices_to_remove:
            if idx >= len(self.parent_window.datasets):
                continue
            ds = self.parent_window.datasets[idx]
            start = ds["start_idx"]
            count = ds["count"]
            
            # Verify all columns are still empty
            all_empty = all(
                len(self.parent_window.data_vars[start + i]) == 0
                for i in range(count)
                if start + i < len(self.parent_window.data_vars)
            )
            if not all_empty:
                continue
                
            # Remove the empty placeholder data
            del self.parent_window.data_vars[start:start + count]
            del self.parent_window.var_names[start:start + count]
            del self.parent_window.datasets[idx]
            
            # Shift subsequent datasets
            for ds2 in self.parent_window.datasets[idx:]:
                ds2["start_idx"] -= count
        
        if indices_to_remove:
            self.parent_window.update_plot()
            
        self._new_dataset_indices.clear()
        super().closeEvent(event)
