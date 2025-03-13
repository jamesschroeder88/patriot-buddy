import json
import os
from Colors import *
from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QDialog, QCheckBox, QLineEdit,
                               QFormLayout, QTabWidget, QScrollArea,QGroupBox)


CONFIG_FILE = "patriot-buddy/patriot_buddy_config.json"

class ApiConfigDialog(QDialog):
    """Dialog for managing API configurations"""

    def __init__(self, parent=None, api_config=None):
        super().__init__(parent)

        self.setWindowTitle("API Configuration")
        self.setMinimumSize(500, 400)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {BACKGROUND_COLOR};
            }}
            QTabWidget::pane {{
                border: 1px solid #d0d0d0;
                background-color: white;
                border-radius: 4px;
            }}
            QTabBar::tab {{
                background-color: #f0f0f0;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            QTabBar::tab:selected {{
                background-color: white;
                border: 1px solid #d0d0d0;
                border-bottom-color: white;
            }}
            QCheckBox {{
                spacing: 8px;
            }}
            QLineEdit {{
                padding: 6px;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
            }}
            QPushButton {{
                background-color: {PRIMARY_COLOR};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {ACCENT_COLOR};
            }}
        """)

        # Load or initialize config
        self.api_config = api_config if api_config else self.load_config()

        # Main layout
        layout = QVBoxLayout(self)

        # Tab widget for different categories
        self.tab_widget = QTabWidget()

        # Create tabs for different API categories
        self.create_api_tab()

        layout.addWidget(self.tab_widget)

        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")

        save_button.clicked.connect(self.save_and_close)
        cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(cancel_button)
        button_layout.addWidget(save_button)

        layout.addLayout(button_layout)

    def create_api_tab(self):
        """Create the tab with API settings"""
        api_widget = QWidget()
        api_layout = QVBoxLayout(api_widget)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        self.api_checkboxes = {}
        self.api_fields = {}

        # Group APIs by category
        for api_id, api_data in self.api_config["apis"].items():
            api_group = QGroupBox(api_data["name"])
            group_layout = QFormLayout(api_group)

            # Enable/disable checkbox
            checkbox = QCheckBox("Enable")
            checkbox.setChecked(api_data["enabled"])
            self.api_checkboxes[api_id] = checkbox

            # API key field
            key_field = QLineEdit(api_data.get("key", ""))
            key_field.setPlaceholderText("Enter API Key")
            self.api_fields[f"{api_id}_key"] = key_field

            group_layout.addRow(checkbox, QWidget())  # Empty widget as spacer
            group_layout.addRow("API Key:", key_field)

            # Add additional fields based on API type
            if api_id == "weather":
                location_field = QLineEdit(api_data.get("default_location", ""))
                location_field.setPlaceholderText("City, Country (e.g. Paris,FR)")
                self.api_fields[f"{api_id}_location"] = location_field
                group_layout.addRow("Default Location:", location_field)

            elif api_id == "stocks":
                symbol_field = QLineEdit(api_data.get("default_symbol", ""))
                symbol_field.setPlaceholderText("Default Stock Symbol (e.g. AAPL)")
                self.api_fields[f"{api_id}_symbol"] = symbol_field
                group_layout.addRow("Default Symbol:", symbol_field)

            # Add more fields for other API types as needed

            scroll_layout.addWidget(api_group)

        scroll_area.setWidget(scroll_content)
        api_layout.addWidget(scroll_area)

        self.tab_widget.addTab(api_widget, "API Settings")

    def save_and_close(self):
        """Save the configuration and close the dialog"""
        # Update configuration based on user input
        for api_id, checkbox in self.api_checkboxes.items():
            self.api_config["apis"][api_id]["enabled"] = checkbox.isChecked()

            # Update API key
            if f"{api_id}_key" in self.api_fields:
                self.api_config["apis"][api_id]["key"] = self.api_fields[f"{api_id}_key"].text()

            # Update additional fields
            if api_id == "weather" and f"{api_id}_location" in self.api_fields:
                self.api_config["apis"][api_id]["default_location"] = self.api_fields[f"{api_id}_location"].text()

            elif api_id == "stocks" and f"{api_id}_symbol" in self.api_fields:
                self.api_config["apis"][api_id]["default_symbol"] = self.api_fields[f"{api_id}_symbol"].text()

        # Save to file
        self.save_config()

        self.accept()

    def load_config(self):
        """Load configuration from file or return default"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")

        return DEFAULT_API_CONFIG

    def save_config(self):
        """Save configuration to file"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.api_config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")