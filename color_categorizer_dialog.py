from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QPushButton, QProgressBar, QFileDialog, QComboBox, QLabel, QMessageBox, QTableWidget, QTableWidgetItem, QColorDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
import json
import os
from qgis.core import QgsProject, QgsSymbol, QgsRendererCategory, QgsCategorizedSymbolRenderer
from PyQt5.QtCore import QSettings

class ColorCategorizerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Color Categorizer')

        # Initialize QSettings
        self.settings = QSettings('PSA-GMD', 'ColorCategorizer')

        layout = QVBoxLayout()

        # Label to show selected JSON path
        self.json_label = QLabel('Select JSON Path:')
        layout.addWidget(self.json_label)

        # JSON file selection button
        self.select_json_button = QPushButton('Browse')
        self.select_json_button.clicked.connect(self.select_json_file)
        layout.addWidget(self.select_json_button)

        # Layer selection dropdown
        self.layer_label = QLabel('Select Layer:')
        layout.addWidget(self.layer_label)
        self.layer_combobox = QComboBox()
        layout.addWidget(self.layer_combobox)

        # Attribute field selection dropdown
        self.attribute_label = QLabel('Select Attribute Field:')
        layout.addWidget(self.attribute_label)
        self.attribute_combobox = QComboBox()
        layout.addWidget(self.attribute_combobox)

        # Table to display color data from JSON
        self.color_table = QTableWidget()
        self.color_table.setColumnCount(2)
        self.color_table.setHorizontalHeaderLabels(['Sub Type', 'Color'])
        self.color_table.itemChanged.connect(self.on_item_changed)  # Connect itemChanged signal
        layout.addWidget(self.color_table)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        layout.addWidget(self.progress_bar)

        # Process button
        self.process_button = QPushButton('Apply Colors')
        self.process_button.clicked.connect(self.process_json_file)
        layout.addWidget(self.process_button)

        # Add version label at the bottom
        version_label = QLabel("GMD | Version: 1.0")
        layout.addWidget(version_label)

        self.setLayout(layout)
        self.json_file_path = None
        self.color_data = None

        # Load previously selected JSON path from QSettings
        self.load_selected_json_path()

        # Initialize layers and attributes
        self.update_layers()

    def load_selected_json_path(self):
        """Load the previously selected JSON file path from QSettings."""
        saved_path = self.settings.value('json_file_path', '')
        if saved_path:
            if os.path.isfile(saved_path):
                self.json_file_path = saved_path
                self.json_label.setText(f'Selected JSON Path: .../{os.path.basename(saved_path)}')
                self.load_json_data()
            else:
                # Show a warning if the JSON file is not found
                QMessageBox.warning(self, 'Warning', f'The previously selected JSON file "{saved_path}" was not found. Please select a new file.')
                self.settings.remove('json_file_path')
        else:
            # No saved path, clear the label
            self.json_label.setText('Select JSON Path:')


    def update_layers(self):
        """Populate the layer dropdown."""
        layers = QgsProject.instance().mapLayers().values()
        
        if not layers:
            QMessageBox.warning(self, 'No Layers', 'No layers available in the project.')
            return

        self.layer_combobox.clear()
        self.layer_combobox.addItems([layer.name() for layer in layers])

        # Connect the layer selection to updating attributes
        self.layer_combobox.currentIndexChanged.connect(self.update_attributes)

        # Set default selected layer if available
        default_layer_name = self.settings.value('default_layer', None)
        if default_layer_name:
            index = self.layer_combobox.findText(default_layer_name)
            if index >= 0:
                self.layer_combobox.setCurrentIndex(index)
                self.update_attributes()  # Ensure attributes are updated
        else:
            # Update attributes for the first available layer by default
            self.update_attributes()

    def update_attributes(self):
        """Update the attribute dropdown based on the selected layer."""
        layer_name = self.layer_combobox.currentText()

        # Ensure the layer exists
        layers = QgsProject.instance().mapLayersByName(layer_name)
        if not layers:
            QMessageBox.warning(self, 'Error', f'Layer "{layer_name}" not found.')
            self.attribute_combobox.clear()
            return

        # Retrieve the first matching layer
        self.layer = layers[0]

        if not self.layer:
            self.attribute_combobox.clear()
            return

        # Fetch field names (attributes) from the selected layer
        fields = self.layer.fields().names()
        
        if not fields:
            QMessageBox.warning(self, 'No Fields', 'The selected layer has no attributes.')
            self.attribute_combobox.clear()
            return

        self.attribute_combobox.clear()
        self.attribute_combobox.addItems(fields)

        # Set default selected attribute field if available
        default_attribute = self.settings.value('default_attribute', None)
        if default_attribute and default_attribute in fields:
            index = self.attribute_combobox.findText(default_attribute)
            if index >= 0:
                self.attribute_combobox.setCurrentIndex(index)


    def select_json_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Select JSON', '', 'JSON Files (*.json)')
        if file_path:
            self.json_file_path = file_path
            self.json_label.setText(f'Selected JSON Path: .../{os.path.basename(file_path)}')
            self.load_json_data()
            # Save the selected JSON file path to QSettings
            self.settings.setValue('json_file_path', file_path)

    def load_json_data(self):
        """Load JSON data and populate the color table."""
        try:
            with open(self.json_file_path, 'r') as file:
                self.color_data = json.load(file)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to load JSON file: {e}')
            return

        # Populate table with key-color pairs
        self.color_table.setRowCount(len(self.color_data))
        for row, (key, color) in enumerate(self.color_data.items()):
            key_item = QTableWidgetItem(key)
            key_item.setFlags(key_item.flags() | Qt.ItemIsEditable)  # Make key column editable
            self.color_table.setItem(row, 0, key_item)

            # Create a button for color selection
            color_button = QPushButton()
            color_button.setStyleSheet(f"background-color: {color}")
            color_button.clicked.connect(lambda _, r=row: self.select_color(r))
            self.color_table.setCellWidget(row, 1, color_button)

    def on_item_changed(self, item):
        """Handle changes in the table items."""
        if item.column() == 0:  # Check if the edited item is in the key column
            new_key = item.text()
            old_key = list(self.color_data.keys())[item.row()]
            if new_key != old_key:
                # Update the color_data dictionary with the new key
                self.color_data[new_key] = self.color_data.pop(old_key)
                self.update_color_table()

    def update_color_table(self):
        """Update the color table to reflect changes in the color_data."""
        self.color_table.blockSignals(True)  # Temporarily block signals to avoid recursion
        self.load_json_data()  # Reload the data
        self.color_table.blockSignals(False)  # Unblock signals

    def select_color(self, row):
        """Open color dialog to allow the user to select a color."""
        current_color = self.color_table.cellWidget(row, 1).palette().button().color()
        color = QColorDialog.getColor(current_color, self, "Select Color")

        if color.isValid():
            # Update the button background color
            color_hex = color.name()
            self.color_table.cellWidget(row, 1).setStyleSheet(f"background-color: {color_hex}")

            # Update the color data with the new color
            key = self.color_table.item(row, 0).text()
            self.color_data[key] = color_hex

    def process_json_file(self):
        """Process the JSON file and apply colors to the selected layer."""
        # Check if a layer is selected
        if not self.layer_combobox.currentText():
            QMessageBox.warning(self, 'Error', 'Please select a layer before applying colors.')
            return

        # Check if the JSON file is selected
        if not self.json_file_path:
            QMessageBox.warning(self, 'Error', 'Please select a JSON file before applying colors.')
            return

        # Retrieve the selected layer
        layer_name = self.layer_combobox.currentText()
        layers = QgsProject.instance().mapLayersByName(layer_name)
        if not layers:
            QMessageBox.warning(self, 'Error', f'Layer "{layer_name}" not found.')
            return

        self.layer = layers[0]

        # Check if an attribute field is selected
        attribute_field_name = self.attribute_combobox.currentText()
        if not attribute_field_name:
            QMessageBox.warning(self, 'Error', 'Please select an attribute field.')
            return

        # Create categories based on the JSON color data
        categories = []
        total_items = len(self.color_data)
        for idx, (key, color) in enumerate(self.color_data.items()):
            symbol = QgsSymbol.defaultSymbol(self.layer.geometryType())
            symbol.setColor(QColor(color))
            category = QgsRendererCategory(key, symbol, key)
            categories.append(category)

            # Update progress bar
            progress_percentage = int((idx + 1) / total_items * 100)
            self.progress_bar.setValue(progress_percentage)

        # Create and apply the categorized renderer
        renderer = QgsCategorizedSymbolRenderer(attribute_field_name, categories)
        self.layer.setRenderer(renderer)
        self.layer.triggerRepaint()

        # Show success message
        QMessageBox.information(self, 'Success', 'Colors have been applied to the layer.')

        # Save the default layer and attribute field to QSettings
        self.settings.setValue('default_layer', self.layer_combobox.currentText())
        self.settings.setValue('default_attribute', self.attribute_combobox.currentText())

