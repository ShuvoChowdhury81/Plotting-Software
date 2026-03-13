import sys
FILE = r"r:\Softwares\Ploting Software\ui\main_window.py"
with open(FILE, "r", encoding="utf-8") as f:
    text = f.read()

bad = '''    def open_mapping_style(self):
        dialog = MappingStyleDialog(self)
        dialog.exec()'''

good = '''    def open_data_table(self):
        if not self.data_vars:
            self.status.showMessage("Please load data before opening Spreadsheet Table.")
            return
        self.data_table_dlg = DataTableDialog(self)
        self.data_table_dlg.show()
        
    def open_mapping_style(self):
        dialog = MappingStyleDialog(self)
        dialog.exec()'''

if bad in text:
    text = text.replace(bad, good)
    with open(FILE, "w", encoding="utf-8") as f:
        f.write(text)
    print("PATCH2 APPLIED")
else:
    print("NOT FOUND")
