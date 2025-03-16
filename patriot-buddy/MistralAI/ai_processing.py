import requests
import json
from PySide6.QtCore import Signal, QObject

class AI_Processor(QObject):
    command = Signal(str, str)

    EVENT_ON = "PLUGON"
    EVENT_OFF = "PLUGOFF"

    selected_mode = None

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

    def process_command(self, text):
        """Process the user's command based on classification or direct mode"""
        if self.selected_mode:
            intent = self.selected_mode
        else:
            intent = self.classify_intent(text)

        # Route to appropriate handler
        if intent == "HOME_AUTOMATION":
            response = self.handle_home_automation(text)
        elif intent == "EXTERNAL_API":
            response = self.handle_external_api(text)
        else:  # Default to conversation
            response = self.handle_conversation(text)

        # Update UI and speak response
        self.command.emit(response, "response")
        

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
                if self.trigger_ifttt(self.EVENT_ON):
                    return "I've turned the lights on for you."
                else:
                    return "I tried to turn the lights on, but there was an error."
            elif device_action == "LIGHTS:OFF":
                if self.trigger_ifttt(self.EVENT_OFF):
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
