import sys
from dotenv import load_dotenv
import threading
import random
import json
import os
from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtGui import QColor, QPainter, QPixmap, QIcon
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel,
                               QWidget, QPushButton, QFrame, QDialog, QCheckBox, QLineEdit,
                               QFormLayout, QTabWidget, QScrollArea, QMessageBox, QGridLayout,
                               QGroupBox)
import requests
import speech_recognition as sr
from elevenlabs.client import ElevenLabs
from elevenlabs import play, VoiceSettings

# Load environment variables
load_dotenv()

# Modern color palette
PRIMARY_COLOR = "#1a7f40"  # Deeper green
SECONDARY_COLOR = "#ffd600"  # Yellow
ACCENT_COLOR = "#134d28"  # Darker green for contrast
BACKGROUND_COLOR = "#fafafa"  # Clean, light background
TEXT_COLOR = "#333333"  # Dark text
LIGHT_TEXT_COLOR = "#666666"  # Secondary text

# Load API keys from environment variables
IFTTT_API_KEY = os.getenv("IFTTT_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = os.getenv("VOICE_ID")
EVENT_ON = "PLUGON"
EVENT_OFF = "PLUGOFF"

# Default API configuration
DEFAULT_API_CONFIG = {
    "apis": {
        "weather": {
            "enabled": True,
            "name": "Weather",
            "provider": "OpenWeatherMap",
            "key": os.getenv("OPENWEATHER_API_KEY"),
            "default_location": "Manassas,VA,US"
        },
        "stocks": {
            "enabled": True,
            "name": "Stocks",
            "provider": "Alpha Vantage",
            "key": "default_key",
            "default_symbol": "AAPL"
        },
        "news": {
            "enabled": False,
            "name": "News",
            "provider": "NewsAPI",
            "key": "default_key",
            "topics": "technology"
        },
        "sports": {
            "enabled": False,
            "name": "Sports Scores",
            "provider": "ESPN",
            "key": "default_key",
            "teams": "Washington"
        },
        "crypto": {
            "enabled": False,
            "name": "Cryptocurrency",
            "provider": "CoinGecko",
            "key": "default_key",
            "default_coin": "bitcoin"
        },
        "traffic": {
            "enabled": False,
            "name": "Traffic",
            "provider": "MapQuest",
            "key": "default_key",
            "route": "home_to_work"
        },
        "calendar": {
            "enabled": False,
            "name": "Calendar",
            "provider": "Google Calendar",
            "key": "default_key",
            "calendar_id": "primary"
        },
        "reminders": {
            "enabled": False,
            "name": "Reminders",
            "provider": "Local Reminders",
            "storage": "reminders.json"
        }
    }
}

# Initialize ElevenLabs client
client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

# Path to save API configuration
CONFIG_FILE = "patriot_buddy_config.json"


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


class ListeningAnimation(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(140, 140)

        # Color scheme
        self.wave_color = QColor(26, 127, 64)  # Green
        self.center_color = QColor(255, 214, 0)  # Yellow

        self.circle_radius = 50
        self.animation_progress = 0.0

        # Animation timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)

        # Wave properties
        self.wave_count = 3
        self.waves = []
        for i in range(self.wave_count):
            self.waves.append(0.0)  # Initial scale values

        self.is_animating = False

    def start_animation(self):
        self.is_animating = True
        self.timer.start(50)  # Update every 50ms

    def stop_animation(self):
        self.is_animating = False
        self.timer.stop()
        # Reset waves
        for i in range(self.wave_count):
            self.waves[i] = 0.0
        self.update()

    def update_animation(self):
        # Update each wave
        for i in range(self.wave_count):
            if self.waves[i] < 1.0:
                self.waves[i] += 0.05
            else:
                self.waves[i] = 0.0
        self.update()

    def paintEvent(self, event):
        if not self.is_animating:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        center_x = self.width() // 2
        center_y = self.height() // 2

        # Draw waves
        for i, scale in enumerate(self.waves):
            if scale > 0:
                opacity = 1.0 - scale
                size = self.circle_radius * (1.0 + scale)

                painter.setPen(Qt.NoPen)
                color = self.wave_color  # Green color
                color.setAlphaF(opacity * 0.5)
                painter.setBrush(color)

                painter.drawEllipse(center_x - size, center_y - size, size * 2, size * 2)

        # Draw center circle
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.center_color)  # Yellow color
        painter.drawEllipse(center_x - self.circle_radius / 2, center_y - self.circle_radius / 2,
                            self.circle_radius, self.circle_radius)


class ModernFrame(QFrame):
    """Custom frame with modern styling"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(f"""
            ModernFrame {{
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
            }}
        """)


class VoiceAssistantGUI(QMainWindow):
    update_signal = Signal(str, str)  # (message, type)

    def __init__(self):
        super().__init__()
        self.is_listening = False
        self.r = sr.Recognizer()
        self.selected_mode = None
        self.api_config = self.load_config()
        self.init_ui()
        self.update_signal.connect(self.update_ui)

    def init_ui(self):
        # Set window properties
        self.setWindowTitle("Patriot Buddy")
        self.setMinimumSize(540, 680)
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {BACKGROUND_COLOR};
            }}
            QLabel {{
                color: {TEXT_COLOR};
                font-family: 'SF Pro Display', 'Segoe UI', Arial, sans-serif;
            }}
        """)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)

        # Top bar with settings button
        top_bar = QWidget()
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(0, 0, 0, 0)

        # Settings button
        settings_button = QPushButton("Settings")
        settings_button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {PRIMARY_COLOR};
                border: 1px solid {PRIMARY_COLOR};
                border-radius: 4px;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background-color: rgba(26, 127, 64, 0.1);
            }}
        """)
        settings_button.clicked.connect(self.open_settings)

        top_layout.addStretch()
        top_layout.addWidget(settings_button)

        main_layout.addWidget(top_bar)

        # Container for logo/animation with click functionality
        self.buddy_container = QPushButton()
        self.buddy_container.setCursor(Qt.PointingHandCursor)
        self.buddy_container.setFixedSize(160, 160)
        self.buddy_container.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.05);
                border-radius: 80px;
            }
        """)
        self.buddy_container.clicked.connect(self.toggle_listening)

        # Logo
        self.logo_label = QLabel(self.buddy_container)
        logo_path = "patriot_buddy.png"
        try:
            pixmap = QPixmap(logo_path)
            pixmap = pixmap.scaled(140, 140, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo_label.setPixmap(pixmap)
            self.logo_label.setGeometry(10, 10, 140, 140)
        except Exception as e:
            print(f"Error loading logo: {e}")
            self.logo_label.setText("Patriot Buddy")
            self.logo_label.setStyleSheet("font-size: 24px; font-weight: bold;")
            self.logo_label.setGeometry(0, 0, 160, 160)
            self.logo_label.setAlignment(Qt.AlignCenter)

        # Animation widget
        self.animation_widget = ListeningAnimation(self.buddy_container)
        self.animation_widget.setGeometry(10, 10, 140, 140)
        self.animation_widget.setVisible(False)  # Hide initially

        main_layout.addWidget(self.buddy_container, 0, Qt.AlignCenter)

        # Status label
        self.status_label = QLabel("Click Patriot Buddy to speak")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet(f"""
            font-size: 16px;
            color: {LIGHT_TEXT_COLOR};
            margin-top: 5px;
        """)
        main_layout.addWidget(self.status_label)

        # Mode selector
        mode_selector = QWidget()
        mode_layout = QHBoxLayout(mode_selector)
        mode_layout.setContentsMargins(0, 0, 0, 10)
        mode_layout.setSpacing(10)

        mode_label = QLabel("Quick select:")
        mode_label.setStyleSheet(f"color: {LIGHT_TEXT_COLOR}; font-size: 14px;")

        button_style = f"""
            QPushButton {{
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 6px 12px;
                color: {TEXT_COLOR};
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: #f5f5f5;
            }}
            QPushButton:pressed {{
                background-color: #e0e0e0;
            }}
        """

        # Normal mode button (new)
        self.normal_button = QPushButton("Normal")
        self.normal_button.setStyleSheet(button_style)
        self.normal_button.clicked.connect(lambda: self.set_direct_mode(None))

        self.chat_button = QPushButton("Chat")
        self.chat_button.setStyleSheet(button_style)
        self.chat_button.clicked.connect(lambda: self.set_direct_mode("CONVERSATION"))

        self.lights_button = QPushButton("Lights")
        self.lights_button.setStyleSheet(button_style)
        self.lights_button.clicked.connect(lambda: self.set_direct_mode("HOME_AUTOMATION"))

        self.data_button = QPushButton("Weather/Stocks")
        self.data_button.setStyleSheet(button_style)
        self.data_button.clicked.connect(lambda: self.set_direct_mode("EXTERNAL_API"))

        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.normal_button)
        mode_layout.addWidget(self.chat_button)
        mode_layout.addWidget(self.lights_button)
        mode_layout.addWidget(self.data_button)
        mode_layout.setAlignment(Qt.AlignCenter)

        main_layout.addWidget(mode_selector)

        # User input display - larger and more modern
        input_container = ModernFrame()
        input_layout = QVBoxLayout(input_container)

        input_header = QLabel("You")
        input_header.setStyleSheet(f"""
            font-size: 14px;
            font-weight: bold;
            color: {PRIMARY_COLOR};
            padding-left: 5px;
        """)

        self.user_input = QLabel("")
        self.user_input.setWordWrap(True)
        self.user_input.setStyleSheet(f"""
            font-size: 18px;
            color: {TEXT_COLOR};
            padding: 10px 5px;
        """)

        input_layout.addWidget(input_header)
        input_layout.addWidget(self.user_input)
        input_container.setFixedHeight(120)
        main_layout.addWidget(input_container)

        # Response display - larger and more modern
        response_container = ModernFrame()
        response_layout = QVBoxLayout(response_container)

        response_header = QLabel("Assistant")
        response_header.setStyleSheet(f"""
            font-size: 14px;
            font-weight: bold;
            color: {PRIMARY_COLOR};
            padding-left: 5px;
        """)

        self.response_display = QLabel("")
        self.response_display.setWordWrap(True)
        self.response_display.setStyleSheet(f"""
            font-size: 18px;
            color: {TEXT_COLOR};
            padding: 10px 5px;
        """)

        response_layout.addWidget(response_header)
        response_layout.addWidget(self.response_display)
        response_container.setFixedHeight(200)  # Taller response box
        main_layout.addWidget(response_container)

        # Highlight Normal mode button initially
        self.set_direct_mode(None)

    def open_settings(self):
        """Open the API configuration dialog"""
        dialog = ApiConfigDialog(self, self.api_config)
        if dialog.exec():
            # If dialog was accepted, reload config
            self.api_config = self.load_config()

    def load_config(self):
        """Load configuration from file or return default"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")

        return DEFAULT_API_CONFIG

    def set_direct_mode(self, mode):
        """Set the direct mode for the next interaction"""
        self.selected_mode = mode

        # Update button styling to show selected mode
        reset_style = f"""
            QPushButton {{
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 6px 12px;
                color: {TEXT_COLOR};
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: #f5f5f5;
            }}
            QPushButton:pressed {{
                background-color: #e0e0e0;
            }}
        """

        selected_style = f"""
            QPushButton {{
                background-color: {PRIMARY_COLOR};
                border: 1px solid {PRIMARY_COLOR};
                border-radius: 4px;
                padding: 6px 12px;
                color: white;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {ACCENT_COLOR};
            }}
            QPushButton:pressed {{
                background-color: {ACCENT_COLOR};
            }}
        """

        self.normal_button.setStyleSheet(reset_style)
        self.chat_button.setStyleSheet(reset_style)
        self.lights_button.setStyleSheet(reset_style)
        self.data_button.setStyleSheet(reset_style)

        if mode is None:
            self.normal_button.setStyleSheet(selected_style)
            mode_text = "Normal"
        elif mode == "CONVERSATION":
            self.chat_button.setStyleSheet(selected_style)
            mode_text = "Chat"
        elif mode == "HOME_AUTOMATION":
            self.lights_button.setStyleSheet(selected_style)
            mode_text = "Lights"
        elif mode == "EXTERNAL_API":
            self.data_button.setStyleSheet(selected_style)
            mode_text = "Weather/Stocks"
        else:
            mode_text = "Normal"

        self.status_label.setText(f"Mode set to {mode_text}. Click Patriot Buddy to speak.")

    def toggle_listening(self):
        if not self.is_listening:
            self.start_listening()
        else:
            self.stop_listening()

    def start_listening(self):
        self.is_listening = True
        self.status_label.setText("Listening...")
        self.logo_label.setVisible(False)  # Hide logo
        self.animation_widget.setVisible(True)  # Show animation
        self.animation_widget.start_animation()
        self.user_input.setText("")
        self.response_display.setText("")

        # Start recording in a separate thread
        threading.Thread(target=self.record_audio, daemon=True).start()

    def stop_listening(self):
        self.is_listening = False
        self.animation_widget.stop_animation()
        self.animation_widget.setVisible(False)  # Hide animation
        self.logo_label.setVisible(True)  # Show logo again

        if self.selected_mode is None:
            mode_text = "Normal"
        elif self.selected_mode == "CONVERSATION":
            mode_text = "Chat"
        elif self.selected_mode == "HOME_AUTOMATION":
            mode_text = "Lights"
        elif self.selected_mode == "EXTERNAL_API":
            mode_text = "Weather/Stocks"
        else:
            mode_text = "Normal"

        self.status_label.setText(f"Mode set to {mode_text}. Click Patriot Buddy to speak.")

    def record_audio(self):
        with sr.Microphone() as source:
            self.r.adjust_for_ambient_noise(source)
            try:
                audio = self.r.listen(source, timeout=5)
                try:
                    text = self.r.recognize_google(audio)
                    self.update_signal.emit(text, "user_input")
                    self.process_command(text)
                except sr.UnknownValueError:
                    self.update_signal.emit("I couldn't understand that. Please try again.", "error")
                except sr.RequestError as e:
                    self.update_signal.emit(f"Speech recognition error: {e}", "error")
            except sr.WaitTimeoutError:
                self.update_signal.emit("No speech detected", "error")

            self.update_signal.emit("", "stop_listening")

    def process_command(self, text):
        """Process the user's command based on classification or direct mode"""
        if self.selected_mode:
            intent = self.selected_mode
        else:
            # Classify intent
            intent = self.classify_intent(text)

        # Route to appropriate handler
        if intent == "HOME_AUTOMATION":
            response = self.handle_home_automation(text)
        elif intent == "EXTERNAL_API":
            response = self.handle_external_api(text)
        else:  # Default to conversation
            response = self.handle_conversation(text)

        # Update UI and speak response
        self.update_signal.emit(response, "response")
        self.speak(response)

    def classify_intent(self, prompt):
        """
        Use Mistral AI to classify the user's intent
        """
        url = "http://localhost:11434/api/generate"
        data = {
            "model": "mistral",
            "prompt": f"""You are an AI assistant that classifies user requests into specific categories. Classify the following request into one of these categories:

            1. CONVERSATION - general chat, questions not requiring external data
            2. HOME_AUTOMATION - controlling lights, thermostats, or other smart home devices
            3. EXTERNAL_API - requests for weather, stocks, news, or other external data

            For the following request, respond with ONLY 'CONVERSATION', 'HOME_AUTOMATION', or 'EXTERNAL_API':
            "{prompt}"

            Response:"""
        }

        try:
            response = requests.post(url, json=data, stream=True)
            full_response = ""
            for line in response.iter_lines():
                if line:
                    json_response = json.loads(line)
                    if 'response' in json_response:
                        full_response += json_response['response']
            return full_response.strip().upper()
        except Exception as e:
            print(f"Error connecting to Mistral for intent classification: {e}")
            return "CONVERSATION"  # Default to conversation on error

    def handle_conversation(self, prompt):
        """
        Use Mistral AI to generate a conversational response
        """
        url = "http://localhost:11434/api/generate"
        data = {
            "model": "mistral",
            "prompt": f"""You are Patriot Buddy, a friendly and helpful assistant. You should keep your responses brief and to the point.

            User: {prompt}
            Patriot Buddy (in 50 words or less):"""
        }

        try:
            response = requests.post(url, json=data, stream=True)
            full_response = ""
            for line in response.iter_lines():
                if line:
                    json_response = json.loads(line)
                    if 'response' in json_response:
                        full_response += json_response['response']
            return full_response.strip()
        except Exception as e:
            print(f"Error connecting to Mistral for conversation: {e}")
            return "I'm having trouble connecting to my thinking module. Can you try again?"

    def handle_home_automation(self, prompt):
        """
        Handle home automation requests
        """
        url = "http://localhost:11434/api/generate"
        data = {
            "model": "mistral",
            "prompt": f"""You are a home automation AI assistant. Based on the user's request, determine what device they want to control and the desired state.

            Currently, you can only control lights (ON or OFF).

            For the following request, respond with ONLY 'LIGHTS:ON', 'LIGHTS:OFF', or 'UNKNOWN':
            "{prompt}"

            Response:"""
        }

        try:
            response = requests.post(url, json=data, stream=True)
            full_response = ""
            for line in response.iter_lines():
                if line:
                    json_response = json.loads(line)
                    if 'response' in json_response:
                        full_response += json_response['response']

            device_action = full_response.strip().upper()

            if device_action == "LIGHTS:ON":
                if self.trigger_ifttt(EVENT_ON):
                    return "I've turned the lights on for you."
                else:
                    return "I tried to turn the lights on, but there was an error."
            elif device_action == "LIGHTS:OFF":
                if self.trigger_ifttt(EVENT_OFF):
                    return "I've turned the lights off for you."
                else:
                    return "I tried to turn the lights off, but there was an error."
            else:
                return "I can only control lights right now. You can ask me to turn them on or off."

        except Exception as e:
            print(f"Error in home automation: {e}")
            return "I had trouble understanding your home automation request."

    def handle_external_api(self, prompt):
        """
        Handle requests requiring external API calls
        """
        url = "http://localhost:11434/api/generate"
        data = {
            "model": "mistral",
            "prompt": f"""You are an AI assistant that identifies what external data a user is requesting.

            1. WEATHER - requesting weather information
            2. STOCKS - requesting stock market information
            3. OTHER - any other external data request

            For the following request, respond with ONLY 'WEATHER', 'STOCKS', or 'OTHER':
            "{prompt}"

            Response:"""
        }

        try:
            response = requests.post(url, json=data, stream=True)
            data_type = ""
            for line in response.iter_lines():
                if line:
                    json_response = json.loads(line)
                    if 'response' in json_response:
                        data_type += json_response['response']

            data_type = data_type.strip().upper()

            if data_type == "WEATHER":
                return self.get_weather(prompt)
            elif data_type == "STOCKS":
                return self.get_stocks(prompt)
            else:
                return "I don't have access to that type of external data yet."

        except Exception as e:
            print(f"Error in external API handler: {e}")
            return "I had trouble connecting to external data sources."

    def get_weather(self, prompt):
        """
        Get weather information using the configured API
        """
        # Check if weather API is enabled
        if not self.api_config["apis"]["weather"]["enabled"]:
            return "Weather information is currently disabled. You can enable it in settings."

        # Get API key and default location
        api_key = self.api_config["apis"]["weather"]["key"]
        default_location = self.api_config["apis"]["weather"]["default_location"]

        # Extract location from prompt
        url = "http://localhost:11434/api/generate"
        data = {
            "model": "mistral",
            "prompt": f"""Extract the location from the following weather request. 
            If no location is explicitly mentioned, respond with 'DEFAULT'.
            Return ONLY the location name, nothing else.

            Request: "{prompt}"

            Location:"""
        }

        try:
            response = requests.post(url, json=data, stream=True)
            location = ""
            for line in response.iter_lines():
                if line:
                    json_response = json.loads(line)
                    if 'response' in json_response:
                        location += json_response['response']

            location = location.strip()
            if location == "DEFAULT":
                location = default_location

            # Call OpenWeatherMap API
            weather_url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=imperial"

            weather_response = requests.get(weather_url)
            if weather_response.status_code == 200:
                weather_data = weather_response.json()
                temp = weather_data["main"]["temp"]
                condition = weather_data["weather"][0]["description"]
                city = weather_data["name"]
                country = weather_data["sys"]["country"]

                return f"It's currently {condition} and {temp}°F in {city}, {country}."
            else:
                # Fallback to mock weather if API call fails
                conditions = ["sunny", "partly cloudy", "overcast", "rainy", "clear"]
                temp = random.randint(65, 85)
                condition = random.choice(conditions)

                return f"Could not get real weather data. Simulated forecast: {condition} and {temp}°F in {location}."

        except Exception as e:
            print(f"Error getting weather: {e}")
            return "I had trouble getting the weather information."

    def get_stocks(self, prompt):
        """
        Get stock information using the configured API
        """
        # Check if stocks API is enabled
        if not self.api_config["apis"]["stocks"]["enabled"]:
            return "Stock information is currently disabled. You can enable it in settings."

        # Extract stock symbol
        url = "http://localhost:11434/api/generate"
        data = {
            "model": "mistral",
            "prompt": f"""Extract the stock symbol or company name from the following stock request.
            Return ONLY the stock symbol or company name, nothing else.

            Request: "{prompt}"

            Stock:"""
        }

        try:
            response = requests.post(url, json=data, stream=True)
            stock = ""
            for line in response.iter_lines():
                if line:
                    json_response = json.loads(line)
                    if 'response' in json_response:
                        stock += json_response['response']

            stock = stock.strip()

            # Mock stock data (would normally call an actual API)
            price = round(random.uniform(50, 500), 2)
            change = round(random.uniform(-3, 5), 2)
            change_percent = round(change / price * 100, 2)

            direction = "up" if change > 0 else "down"

            return f"{stock} is trading at ${price}, {direction} {abs(change_percent)}%. Trading volume is moderate today."

        except Exception as e:
            print(f"Error getting stock information: {e}")
            return "I had trouble getting the stock information."

    def trigger_ifttt(self, event_name):
        """
        Trigger an IFTTT event
        """
        webhook_url = f"https://maker.ifttt.com/trigger/{event_name}/with/key/{IFTTT_API_KEY}"
        try:
            response = requests.post(webhook_url)
            return response.status_code == 200
        except Exception as e:
            print(f"IFTTT Error: {e}")
            return False

    @Slot(str, str)
    def update_ui(self, message, message_type):
        if message_type == "user_input":
            self.user_input.setText(message)
        elif message_type == "response":
            self.response_display.setText(message)
        elif message_type == "error":
            self.status_label.setText(message)
            QTimer.singleShot(2000, lambda: self.status_label.setText("Click Patriot Buddy to speak"))
        elif message_type == "stop_listening":
            self.stop_listening()

    def speak(self, text):
        # Use a thread to avoid blocking the UI
        threading.Thread(target=self._speak_thread, args=(text,), daemon=True).start()

    def _speak_thread(self, text):
        try:
            audio = client.text_to_speech.convert(
                text=text,
                voice_id=VOICE_ID,
                model_id="eleven_multilingual_v2",
                output_format="mp3_44100_128",
                voice_settings=VoiceSettings(
                    stability=0.5,
                    similarity_boost=0.75
                )
            )
            play(audio)
        except Exception as e:
            print(f"Text-to-speech error: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VoiceAssistantGUI()
    window.show()
    sys.exit(app.exec())