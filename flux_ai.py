import os
import sys
import json
from typing import Optional, Tuple
from pathlib import Path
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import logging
import xml.etree.ElementTree as ET
import re
import subprocess as sub
import requests
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from gtts import gTTS
import pygame
import time
import platform

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global language variable
language = "English"

class ConfigManager:
    """Manages application configuration"""
    
    def __init__(self):
        self.config_dir = Path.home() / ".flux_ai_chat"
        self.config_file = self.config_dir / "config.json"
        self.ensure_config_dir()
        self.load_config()
    
    def ensure_config_dir(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def load_config(self):
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            except:
                self.config = self.get_default_config()
        else:
            self.config = self.get_default_config()
            self.save_config()
    
    def get_default_config(self):
        return {
            "api_keys": {"gemini": "", "weather": ""},
            "preferences": {"language": "English", "voice_enabled": False, "voice_volume": 0.7},
            "advanced": {"model": "gemini-1.5-flash", "temperature": 0.7, "max_tokens": 2048}
        }
    
    def save_config(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            return True
        except:
            return False
    
    def get(self, key_path, default=None):
        keys = key_path.split('.')
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    def set(self, key_path, value):
        keys = key_path.split('.')
        config = self.config
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        config[keys[-1]] = value
        self.save_config()

def detect_system_info():
    system = platform.system()
    if system == "Linux":
        try:
            import distro
            return f"{distro.name()} {distro.version()}"
        except:
            return "Linux"
    return system

def play_voice(text, volume=0.7, lang="en"):
    try:
        temp_dir = Path.home() / ".flux_ai_chat" / "temp_voice"
        temp_dir.mkdir(parents=True, exist_ok=True)
        tts = gTTS(text, lang=lang)
        temp_file = temp_dir / "voice.mp3"
        tts.save(str(temp_file))
        pygame.mixer.init()
        pygame.mixer.music.load(str(temp_file))
        pygame.mixer.music.set_volume(min(1.0, max(0.0, volume)))
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.01)
        pygame.quit()
        temp_file.unlink(missing_ok=True)
    except Exception as e:
        logger.error(f"Voice error: {e}")

class SettingsDialog(QDialog):
    def __init__(self, parent=None, config_manager=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.setWindowTitle("Settings")
        self.setFixedSize(600, 500)
        self.setStyleSheet("""
            QDialog {
                background: #0f0f0f;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                font-size: 14px;
            }
            QLineEdit {
                background: #1a1a1a;
                border: 2px solid #333;
                color: white;
                padding: 12px;
                font-size: 14px;
                border-radius: 8px;
                min-height: 25px;
            }
            QLineEdit:focus {
                border: 2px solid #00c853;
            }
            QComboBox {
                background: #1a1a1a;
                border: 2px solid #333;
                color: white;
                padding: 10px;
                font-size: 14px;
                border-radius: 8px;
                min-width: 200px;
                min-height: 25px;
            }
            QComboBox:hover {
                border: 2px solid #00c853;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 6px solid #00c853;
            }
            QComboBox QAbstractItemView {
                background: #1a1a1a;
                color: white;
                selection-background-color: #00c853;
            }
            QCheckBox {
                color: white;
                font-size: 14px;
                spacing: 10px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                background: #1a1a1a;
                border: 2px solid #333;
                border-radius: 4px;
            }
            QCheckBox::indicator:checked {
                background: #00c853;
                border: 2px solid #00c853;
            }
            QPushButton {
                background: #1a1a1a;
                color: white;
                border: 2px solid #333;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: bold;
                border-radius: 6px;
                min-width: 80px;
                min-height: 30px;
                text-align: center;
            }
            QPushButton:hover {
                background: #00b248;
                color: white;
                border: 2px solid #00b248;
            }
            QTabWidget::pane {
                background: #0f0f0f;
                border: 2px solid #333;
            }
            QTabBar::tab {
                background: #1a1a1a;
                color: white;
                padding: 9px 18px;
                margin: 2px;
                font-size: 13px;
                font-weight: bold;
                min-height: 32px;
            }
            QTabBar::tab:selected {
                background: #00c853;
                color: white;
            }
        """)
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        tabs = QTabWidget()
        
        # API Keys Tab
        api_widget = QWidget()
        api_layout = QFormLayout()
        api_layout.setSpacing(20)
        
        self.gemini_key_input = QLineEdit()
        self.gemini_key_input.setEchoMode(QLineEdit.Password)
        self.gemini_key_input.setPlaceholderText("Enter your Gemini API key...")
        
        self.show_gemini_key = QCheckBox("Show key")
        self.show_gemini_key.toggled.connect(
            lambda checked: self.gemini_key_input.setEchoMode(
                QLineEdit.Normal if checked else QLineEdit.Password
            )
        )
        
        self.weather_key_input = QLineEdit()
        self.weather_key_input.setEchoMode(QLineEdit.Password)
        self.weather_key_input.setPlaceholderText("Enter your Weather API key (optional)...")
        
        self.show_weather_key = QCheckBox("Show key")
        self.show_weather_key.toggled.connect(
            lambda checked: self.weather_key_input.setEchoMode(
                QLineEdit.Normal if checked else QLineEdit.Password
            )
        )
        
        api_layout.addRow(QLabel("Gemini API Key:"), self.gemini_key_input)
        api_layout.addRow("", self.show_gemini_key)
        api_layout.addRow(QLabel("Weather API Key:"), self.weather_key_input)
        api_layout.addRow("", self.show_weather_key)
        
        api_widget.setLayout(api_layout)
        tabs.addTab(api_widget, "API Keys")
        
        # Preferences Tab
        pref_widget = QWidget()
        pref_layout = QFormLayout()
        pref_layout.setSpacing(20)
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(["English", "Turkish", "Spanish", "German", "French", "Russian"])
        
        self.voice_enabled = QCheckBox("Enable voice output")
        
        self.voice_volume = QSlider(Qt.Horizontal)
        self.voice_volume.setRange(0, 100)
        self.voice_volume.setValue(70)
        self.volume_label = QLabel("70%")
        self.voice_volume.valueChanged.connect(lambda v: self.volume_label.setText(f"{v}%"))
        
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(self.voice_volume)
        volume_layout.addWidget(self.volume_label)
        
        pref_layout.addRow(QLabel("Language:"), self.language_combo)
        pref_layout.addRow(self.voice_enabled)
        pref_layout.addRow(QLabel("Voice Volume:"), volume_layout)
        
        pref_widget.setLayout(pref_layout)
        tabs.addTab(pref_widget, "Preferences")
        
        layout.addWidget(tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton("Save")
        save_btn.setStyleSheet("""
            QPushButton {
                background: #00c853;
                color: white;
                border: none;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: bold;
                border-radius: 6px;
                min-width: 90px;
                min-height: 30px;
                text-align: center;
            }
            QPushButton:hover {
                background: #00b248;
            }
        """)
        save_btn.clicked.connect(self.save_settings)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def load_settings(self):
        self.gemini_key_input.setText(self.config_manager.get("api_keys.gemini", ""))
        self.weather_key_input.setText(self.config_manager.get("api_keys.weather", ""))
        self.language_combo.setCurrentText(self.config_manager.get("preferences.language", "English"))
        self.voice_enabled.setChecked(self.config_manager.get("preferences.voice_enabled", False))
        self.voice_volume.setValue(int(self.config_manager.get("preferences.voice_volume", 0.7) * 100))
    
    def save_settings(self):
        self.config_manager.set("api_keys.gemini", self.gemini_key_input.text())
        self.config_manager.set("api_keys.weather", self.weather_key_input.text())
        self.config_manager.set("preferences.language", self.language_combo.currentText())
        self.config_manager.set("preferences.voice_enabled", self.voice_enabled.isChecked())
        self.config_manager.set("preferences.voice_volume", self.voice_volume.value() / 100)
        
        global language
        language = self.language_combo.currentText()
        
        QMessageBox.information(self, "Success", "Settings saved successfully!")
        self.accept()

class GeminiChatBot:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.model = None
        self.initialize_model()
    
    def initialize_model(self):
        api_key = self.config_manager.get("api_keys.gemini")
        if not api_key:
            raise ValueError("Gemini API key not configured")
        
        os.environ["GOOGLE_API_KEY"] = api_key
        
        try:
            self.model = ChatGoogleGenerativeAI(
                model=self.config_manager.get("advanced.model", "gemini-2.5-flash"),
                temperature=self.config_manager.get("advanced.temperature", 0.7),
                max_tokens=self.config_manager.get("advanced.max_tokens", 2048)
            )
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            raise
    
    def process_request(self, user_input: str, system_prompt: str) -> Optional[str]:
        try:
            prompt_template = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("user", "{user_input}")
            ])
            chain = prompt_template | self.model | StrOutputParser()
            result = chain.invoke({"user_input": user_input})
            return result
        except Exception as e:
            logger.error(f"Error: {e}")
            return None

class ChatWorker(QThread):
    finished = pyqtSignal(tuple)
    error = pyqtSignal(str)
    
    def __init__(self, chat_bot, agent_type, user_input, config_manager):
        super().__init__()
        self.chat_bot = chat_bot
        self.agent_type = agent_type
        self.user_input = user_input
        self.config_manager = config_manager
    
    def run(self):
        try:
            if self.agent_type == "linux_command":
                result = linux_command(self.user_input, self.chat_bot)
            elif self.agent_type == "weather_gether":
                result = weather_gether(self.user_input, self.chat_bot, self.config_manager)
            elif self.agent_type == "tech_chat":
                result = tech_chat(self.user_input, self.chat_bot)
            self.finished.emit((self.agent_type, result))
        except Exception as e:
            self.error.emit(str(e))

def linux_command(user_input: str, chat_bot) -> Tuple[str, str, str]:
    system_info = detect_system_info()
    
    system_prompt = f"""
    You are a professional Linux system administrator with expertise and humor.
    System: {system_info}
    Response Language: {language}
    
    Provide Linux commands in this XML format:
    <command>
        <linux>exact_command_here</linux>
        <description>Professional explanation with humor when appropriate</description>
    </command>
    
    Be accurate, add subtle humor (xkcd style), warn about dangerous commands.
    """
    
    response = chat_bot.process_request(user_input, system_prompt)
    if not response:
        raise ValueError("No response")
    
    try:
        cleaned_data = re.sub(r'```', '', response)
        root = ET.fromstring(cleaned_data)
        linux_command = root.find('linux').text
        description = root.find('description').text
        
        dangerous_commands = ['rm -rf /', 'dd if=/dev/zero', ':(){ :|:& };:', 'mkfs.']
        is_dangerous = any(cmd in linux_command for cmd in dangerous_commands)
        
        if is_dangerous:
            terminal_output = "⚠️ DANGEROUS COMMAND - Not executed"
        else:
            try:
                terminal_output = sub.check_output(
                    linux_command, shell=True, text=True, 
                    timeout=10, stderr=sub.STDOUT
                )
                terminal_output = f"✅ Output:\n{terminal_output.strip()}"
            except sub.TimeoutExpired:
                terminal_output = "⏱️ Command timed out"
            except Exception as e:
                terminal_output = f"❌ Error: {str(e)}"
        
        return linux_command, description, terminal_output
    except Exception as e:
        logger.error(f"Command error: {e}")
        raise

def weather_gether(user_input: str, chat_bot, config_manager) -> str:
    weather_api = config_manager.get("api_keys.weather")
    if not weather_api:
        return "Weather API key not configured"
    
    system_prompt = """Extract city name. Return XML:
    <weather_request><city>CityName</city></weather_request>
    Or: <weather_request><e>No city</e></weather_request>"""
    
    response = chat_bot.process_request(user_input, system_prompt)
    if not response:
        return "Failed to process"
    
    try:
        root = ET.fromstring(response)
        if root.find('error') is not None:
            return "Please specify a city"
        
        location = root.find('city').text
        url = "https://api.weatherapi.com/v1/forecast.json"
        response = requests.get(url, params={
            "key": weather_api, "q": location, "days": 3
        }, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        current = data['current']
        location_data = data['location']
        
        return f"""
🌍 {location_data['name']}, {location_data['country']}
🌡️ {current['temp_c']}°C (Feels: {current['feelslike_c']}°C)
☁️ {current['condition']['text']}
💨 Wind: {current['wind_kph']} km/h
💧 Humidity: {current['humidity']}%
        """
    except Exception as e:
        return f"Error: {str(e)}"

def tech_chat(user_input: str, chat_bot) -> str:
    system_prompt = f"""
    You are a senior Linux engineer with expertise and dry humor.
    Response Language: {language}
    Be direct, technical but approachable. Keep responses 2-4 sentences.
    Add subtle humor when appropriate. "There is no cloud, it's just someone else's computer."
    """
    
    response = chat_bot.process_request(user_input, system_prompt)
    return response if response else "AI hamsters stopped running. Try again?"

def agent_selector(chat_bot, user_input: str) -> str:
    system_prompt = """
    Classify and return ONLY one:
    'linux_command': Linux/Unix commands
    'weather_gether': Weather info
    'tech_chat': General tech/chat
    """
    
    response = chat_bot.process_request(user_input, system_prompt)
    if not response:
        return "tech_chat"
    
    agent = response.strip().lower()
    return agent if agent in ['linux_command', 'weather_gether', 'tech_chat'] else "tech_chat"

class FluxAIChatGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.chat_bot = None
        self.init_ui()
        self.initialize_chatbot()
    
    def init_ui(self):
        self.setWindowTitle("Flux AI Chat")
        self.setMinimumSize(1000, 800)
        
        # Set window icon from local icons folder
        if os.path.exists("icons/icon.png"):
            self.setWindowIcon(QIcon("icons/icon.png"))
        elif os.path.exists("/usr/share/flux-ai-chat/icons/icon.png"):
            self.setWindowIcon(QIcon("/usr/share/flux-ai-chat/icons/icon.png"))
        
        # Main dark style
        self.setStyleSheet("""
            QWidget {
                background: #0a0a0a;
                color: #ffffff;
                font-family: 'Segoe UI', Ubuntu, sans-serif;
            }
        """)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Top controls
        top_bar = QWidget()
        top_bar.setFixedHeight(50)
        top_bar.setStyleSheet("""
            QWidget {
                background: #141414;
                border-bottom: 2px solid #00c853;
            }
        """)
        
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(20, 10, 20, 10)
        
        # Language selector
        lang_label = QLabel("Language:")
        lang_label.setStyleSheet("color: #00c853; font-weight: bold; font-size: 14px;")
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(["English", "Turkish", "Spanish", "German", "French", "Russian"])
        self.language_combo.setStyleSheet("""
            QComboBox {
                background: #1a1a1a;
                border: 2px solid #333;
                color: white;
                padding: 8px 15px;
                font-size: 13px;
                border-radius: 6px;
                min-width: 120px;
            }
            QComboBox:hover {
                border: 2px solid #00c853;
            }
            QComboBox::drop-down {
                border: none;
                width: 25px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #00c853;
            }
            QComboBox QAbstractItemView {
                background: #1a1a1a;
                color: white;
                selection-background-color: #00c853;
            }
        """)
        self.language_combo.currentTextChanged.connect(self.change_language)
        
        # Voice toggle
        self.voice_btn = QPushButton("🔊 Voice: OFF")
        self.voice_btn.setCheckable(True)
        self.voice_btn.setStyleSheet("""
            QPushButton {
                background: #1f1f1f;
                color: #ffffff;
                border: 2px solid #333;
                padding: 6px 12px;
                font-size: 12px;
                border-radius: 6px;
                font-weight: bold;
                min-width: 110px;
                min-height: 30px;
                text-align: center;
            }
            QPushButton:checked {
                background: #00c853;
                color: #ffffff;
                border: 2px solid #00c853;
            }
            QPushButton:hover {
                border: 2px solid #00c853;
            }
        """)
        self.voice_btn.toggled.connect(self.toggle_voice)
        # Ensure voice starts OFF and readable
        self.voice_btn.setChecked(False)
        self.config_manager.set("preferences.voice_enabled", False)
        
        # Settings button
        settings_btn = QPushButton("⚙️ Settings")
        settings_btn.setStyleSheet("""
            QPushButton {
                background: #00c853;
                color: white;
                border: none;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: bold;
                border-radius: 6px;
                min-height: 30px;
                min-width: 110px;
                text-align: center;
            }
            QPushButton:hover {
                background: #00b248;
            }
        """)
        settings_btn.clicked.connect(self.open_settings)
        
        top_layout.addWidget(lang_label)
        top_layout.addWidget(self.language_combo)
        top_layout.addWidget(self.voice_btn)
        top_layout.addStretch()
        top_layout.addWidget(settings_btn)
        
        top_bar.setLayout(top_layout)
        main_layout.addWidget(top_bar)
        
        # Banner image
        banner_widget = QWidget()
        banner_widget.setFixedHeight(320)
        banner_widget.setStyleSheet("background: #0f0f0f;")
        banner_layout = QVBoxLayout()
        
        # Check for banner in both locations
        banner_paths = [
            "icons/banner.png",
            "/usr/share/flux-ai-chat/icons/banner.png"
        ]
        
        banner_found = False
        for banner_path in banner_paths:
            if os.path.exists(banner_path):
                banner_label = QLabel()
                pixmap = QPixmap(banner_path)
                scaled_pixmap = pixmap.scaled(
                    1300, 300,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                banner_label.setPixmap(scaled_pixmap)
                banner_label.setAlignment(Qt.AlignCenter)
                banner_layout.addWidget(banner_label)
                banner_found = True
                break
        
        if not banner_found:
            # Fallback text banner
            title = QLabel("FLUX AI CHAT")
            title.setStyleSheet("""
                QLabel {
                    color: #00c853;
                    font-size: 60px;
                    font-weight: bold;
                    letter-spacing: 5px;
                }
            """)
            title.setAlignment(Qt.AlignCenter)
            
            subtitle = QLabel("Professional Linux Assistant with Gemini AI")
            subtitle.setStyleSheet("""
                QLabel {
                    color: #a0a0a0;
                    font-size: 20px;
                }
            """)
            subtitle.setAlignment(Qt.AlignCenter)
            
            banner_layout.addStretch()
            banner_layout.addWidget(title)
            banner_layout.addWidget(subtitle)
            banner_layout.addStretch()
        
        banner_widget.setLayout(banner_layout)
        main_layout.addWidget(banner_widget)
        
        # Chat display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background: #0f0f0f;
                color: #ffffff;
                border: none;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 14px;
                padding: 20px;
                line-height: 1.5;
            }
            QScrollBar:vertical {
                background: #1a1a1a;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #333;
                border-radius: 6px;
                min-height: 40px;
            }
            QScrollBar::handle:vertical:hover {
                background: #00c853;
            }
        """)
        self.chat_display.setHtml("""
            <p style='color: #00c853; text-align: center; font-size: 16px;'>
                Welcome to Flux AI Chat!<br>
                <span style='color: #888; font-size: 14px;'>Type a Linux command or ask me anything...</span>
            </p>
        """)
        main_layout.addWidget(self.chat_display)
        
        # Input area
        input_widget = QWidget()
        input_widget.setFixedHeight(80)
        input_widget.setStyleSheet("""
            QWidget {
                background: #141414;
                border-top: 2px solid #00c853;
            }
        """)
        
        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(20, 15, 20, 15)
        input_layout.setSpacing(15)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type your message here...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                background: #1a1a1a;
                color: white;
                border: 2px solid #333;
                padding: 15px;
                font-size: 14px;
                border-radius: 8px;
            }
            QLineEdit:focus {
                border: 2px solid #00c853;
                background: #0f0f0f;
            }
        """)
        self.input_field.returnPressed.connect(self.send_message)
        
        self.send_btn = QPushButton("Send")
        self.send_btn.setStyleSheet("""
            QPushButton {
                background: #00c853;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
                border-radius: 8px;
                min-width: 96px;
                min-height: 34px;
                text-align: center;
            }
            QPushButton:hover {
                background: #00b248;
            }
            QPushButton:disabled {
                background: #333;
                color: #666;
            }
        """)
        self.send_btn.clicked.connect(self.send_message)
        
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_btn)
        
        input_widget.setLayout(input_layout)
        main_layout.addWidget(input_widget)
        
        self.setLayout(main_layout)
    
    def change_language(self, lang):
        global language
        language = lang
        self.config_manager.set("preferences.language", lang)
    
    def toggle_voice(self, checked):
        self.config_manager.set("preferences.voice_enabled", checked)
        self.voice_btn.setText(f"🔊 Voice: {'ON' if checked else 'OFF'}")
    
    def open_settings(self):
        dialog = SettingsDialog(self, self.config_manager)
        if dialog.exec_():
            self.initialize_chatbot()
    
    def initialize_chatbot(self):
        try:
            self.chat_bot = GeminiChatBot(self.config_manager)
        except Exception as e:
            if "not configured" in str(e):
                QMessageBox.information(self, "Setup Required", 
                    "Welcome! Please configure your API keys in Settings.")
    
    def send_message(self):
        message = self.input_field.text().strip()
        if not message:
            return
        
        if not self.chat_bot:
            QMessageBox.warning(self, "Setup Required", 
                "Please configure your API keys in Settings first.")
            return
        
        self.input_field.clear()
        self.send_btn.setEnabled(False)
        
        # Add user message
        timestamp = QDateTime.currentDateTime().toString("HH:mm")
        self.chat_display.append(f"""
            <div style='text-align: right; margin: 10px 0;'>
                <span style='color: #666; font-size: 12px;'>{timestamp}</span><br>
                <span style='background: #1a1a1a; color: white; padding: 10px; 
                      border-radius: 10px; border-left: 3px solid #00c853;'>
                    {message}
                </span>
            </div>
        """)
        
        try:
            agent_type = agent_selector(self.chat_bot, message)
            self.worker = ChatWorker(self.chat_bot, agent_type, message, self.config_manager)
            self.worker.finished.connect(self.handle_response)
            self.worker.error.connect(self.handle_error)
            self.worker.start()
        except Exception as e:
            self.handle_error(str(e))
    
    def handle_response(self, result):
        agent_type, response = result
        timestamp = QDateTime.currentDateTime().toString("HH:mm")
        
        if agent_type == "linux_command":
            cmd, desc, output = response
            html = f"""
                <div style='margin: 10px 0;'>
                    <span style='color: #00c853; font-weight: bold;'>🤖 Flux AI</span>
                    <span style='color: #666; font-size: 12px;'> {timestamp}</span><br>
                    <div style='background: #1a1a1a; padding: 15px; border-radius: 10px; 
                         border-left: 3px solid #00c853; margin-top: 5px;'>
                        <b style='color: #00c853;'>Command:</b> 
                        <code style='color: #0f0;'>{cmd}</code><br><br>
                        <b style='color: #00c853;'>Description:</b> {desc}<br><br>
                        <b style='color: #00c853;'>Output:</b><br>
                        <pre style='color: #0f0; background: #0f0f0f; padding: 10px; 
                             border-radius: 5px;'>{output}</pre>
                    </div>
                </div>
            """
            
            if self.config_manager.get("preferences.voice_enabled", False):
                self.speak_text(f"{desc}. {output}")
        else:
            html = f"""
                <div style='margin: 10px 0;'>
                    <span style='color: #00c853; font-weight: bold;'>🤖 Flux AI</span>
                    <span style='color: #666; font-size: 12px;'> {timestamp}</span><br>
                    <div style='background: #1a1a1a; padding: 15px; border-radius: 10px; 
                         border-left: 3px solid #00c853; margin-top: 5px;'>
                        {response.replace(chr(10), '<br>')}
                    </div>
                </div>
            """
            
            if self.config_manager.get("preferences.voice_enabled", False):
                self.speak_text(response)
        
        self.chat_display.append(html)
        self.send_btn.setEnabled(True)
    
    def handle_error(self, error):
        self.chat_display.append(f"""
            <div style='color: #ff3366; text-align: center; margin: 10px;'>
                ❌ Error: {error}
            </div>
        """)
        self.send_btn.setEnabled(True)
    
    def speak_text(self, text):
        lang_codes = {
            "English": "en", "Turkish": "tr", "Spanish": "es",
            "German": "de", "French": "fr", "Russian": "ru"
        }
        QTimer.singleShot(100, lambda: play_voice(
            text, 
            self.config_manager.get("preferences.voice_volume", 0.7),
            lang_codes.get(language, "en")
        ))

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = FluxAIChatGUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()