from ListeningAnimation import ListeningAnimation
from APIconfigDialog import ApiConfigDialog
from Listener import Listener
from Colors import *
from modernFrame import ModernFrame
from dotenv import load_dotenv
from API_CONFIGS import DEFAULT_API_CONFIG
import threading
import random
import json
import os
from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QWidget, QPushButton)
import requests
from elevenlabs.client import ElevenLabs
from elevenlabs import play, VoiceSettings
from MistralAI.ai_processing import AI_Processor

CONFIG_FILE = "patriot-buddy/patriot_buddy_config.json"

class VoiceAssistantGUI(QMainWindow):
    update_signal = Signal(str, str)  # (message, type)

    load_dotenv(dotenv_path="patriot-buddy/env")

    # Load API keys from environment variables
    IFTTT_API_KEY = os.getenv("IFTTT_API_KEY")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    VOICE_ID = os.getenv("VOICE_ID")
    EVENT_ON = "PLUGON"
    EVENT_OFF = "PLUGOFF"

    # Initialize ElevenLabs client
    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

    def __init__(self):
        super().__init__()

        self.listener = Listener()
        self.listener.text_received.connect(self.process_text)

        self.aiProcessor = AI_Processor()        
        self.aiProcessor.command.connect(self.process_command)

        self.selected_mode = None
        self.api_config = self.load_config()
        self.init_ui()
        self.update_signal.connect(self.update_ui)

    def init_ui(self):
        # Set window properties
        self.setWindowTitle("Patriot Buddy")
        self.setWindowIcon(QPixmap("patriot-buddy/patriot_buddy.ico"))
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
        self.buddy_container.clicked.connect(self.checkListener)

        # Logo
        self.logo_label = QLabel(self.buddy_container)
        logo_path = "patriot-buddy/patriot_buddy.png"
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

    def startListeningChangeUI(self):
        self.status_label.setText("Listening...")
        self.logo_label.setVisible(False)
        self.animation_widget.setVisible(True)  
        self.animation_widget.start_animation()
        self.user_input.setText("")
        self.response_display.setText("")

    def stopListeningChangeUI(self):
        self.animation_widget.stop_animation()
        self.animation_widget.setVisible(False)  
        self.logo_label.setVisible(True)  

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

    def checkListener(self):
        check = self.listener.toggle_listening()

        if check == "Listening":
            self.startListeningChangeUI()
            #self.update_signal.emit(self.Listener.text_received)
        else:
            self.stopListeningChangeUI()


    def open_settings(self):
        dialog = ApiConfigDialog(self, self.api_config)
        if dialog.exec():
            self.api_config = self.load_config()

    def load_config(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")

        return DEFAULT_API_CONFIG
    
    def process_text(self, text, messageType):
        print("Message Type: ", messageType)
        print("Processing Text :", text)
        self.update_signal.emit(text, messageType)
        threading.Thread(target=self.aiProcessor.process_command, args=(text,), daemon=True).start()

    def set_direct_mode(self, mode):
        """Set the direct mode for the next interaction"""
        self.selected_mode = mode

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

    def process_command(self, text):
        self.response_display.setText(text)
        self.speak(text)
  
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
            self.Listener.stop_listening()
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

    def speak(self, text):
        # Use a thread to avoid blocking the UI
        threading.Thread(target=self._speak_thread, args=(text,), daemon=True).start()

    def _speak_thread(self, text):
        try:
            audio = self.client.text_to_speech.convert(
                text=text,
                voice_id=self.VOICE_ID,
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

