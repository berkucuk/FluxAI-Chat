## Flux AI Chat

Flux AI Chat is a desktop AI assistant for Linux built with PyQt5 and Google Gemini via LangChain. It provides a polished chat UI, voice output, and specialized agents for Linux command generation/execution, weather retrieval, and technical Q&A.

### Highlights
- **Modern desktop app**: PyQt5 UI with dark theme, banner, and desktop launcher.
- **Multiple agents**:
  - **Linux Command**: Generates and (safely) executes shell commands with explanations.
  - **Weather**: Fetches 3‑day forecasts via WeatherAPI.
  - **Tech Chat**: Short, expert answers with a touch of humor.
- **Voice output**: Optional TTS using gTTS + pygame with adjustable volume and language.
- **Config UI**: In‑app Settings for API keys, language, voice, and model parameters.

---

### Screenshots
The app uses `icons/banner.png` and `icons/icon.png`. If the banner is missing, a text banner is rendered. You can add your own banner to `icons/banner.png` to customize the look.

---

### Requirements
- Linux desktop (X11 or Wayland)
- Python 3.10+ (system or virtualenv)
- Internet access (for Gemini and Weather APIs)

The installer supports Arch‑based (pacman) and Debian/Ubuntu‑based (apt) systems.

---

### Quick Start (Recommended)
This installs a self‑contained virtual environment under `/usr/share/flux-ai-chat` and creates a desktop launcher.

```bash
chmod +x install.sh
./install.sh
```

After installation:
- Launch from your applications menu as “Flux AI Chat”, or
- Run directly: `/usr/share/flux-ai-chat/python-env/bin/python3 /usr/share/flux-ai-chat/flux_ai.py`

On first run, open Settings and add your API keys.

---

### Run From Source (Dev)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python flux_ai.py
```

---

### Configuration
Configuration is stored at `~/.flux_ai_chat/config.json` and managed via the in‑app Settings dialog.

- **API Keys**
  - **Gemini**: Required. Obtain a key from Google AI Studio, then add it in Settings → API Keys.
  - **Weather**: Optional. Obtain from WeatherAPI and add in Settings to enable weather forecasts.

- **Preferences**
  - **Language**: English, Turkish, Spanish, German, French, Russian. Affects response language and TTS locale.
  - **Voice output**: Toggle ON/OFF. Set volume (0–100%).

- **Advanced**
  - **Model**: Defaults to `gemini-1.5-flash` (or `gemini-2.5-flash` if set). You can change the model name in Settings.
  - **Temperature / Max tokens**: Tunable generation parameters.

You can also edit `~/.flux_ai_chat/config.json` directly if needed.

---

### Usage
1. Launch the app.
2. Open Settings and configure the Gemini API key (required). Optionally add a Weather API key.
3. Choose your UI/voice language from the top bar.
4. Type a prompt and press Enter.

The app automatically classifies your input and routes it to one of the agents below.

---

### Agents & Behavior
- **Linux Command (`linux_command`)**
  - System prompt asks Gemini to return XML:
    ```xml
    <command>
      <linux>exact_command_here</linux>
      <description>…</description>
    </command>
    ```
  - The command is shown with a description and executed in a sandboxed subprocess with a 10s timeout.
  - A small deny‑list prevents obviously dangerous commands (e.g., `rm -rf /`, `dd if=/dev/zero`, fork bombs, `mkfs.*`).
  - Output or error is rendered in the chat. Use with caution; the deny‑list is not exhaustive.

- **Weather (`weather_gether`)**
  - Extracts city name via Gemini and calls `https://api.weatherapi.com/v1/forecast.json` for a 3‑day summary.
  - Requires a WeatherAPI key in Settings.

- **Tech Chat (`tech_chat`)**
  - Senior‑level Linux/infra Q&A in 2–4 sentences with dry humor.

- **Voice**
  - If enabled, responses are spoken using gTTS in your selected language. Volume is adjustable.

---

### Project Structure
```
FluxAI-Chat/
  flux_ai.py            # Main PyQt5 application
  install.sh            # Installer (creates venv + desktop launcher)
  Flux-AI.desktop       # Desktop entry template
  requirements.txt      # Python dependencies
  icons/
    banner.png
    icon.png
```

Key modules/classes in `flux_ai.py`:
- `ConfigManager`: Loads/saves `~/.flux_ai_chat/config.json` and provides getters/setters.
- `GeminiChatBot`: LangChain wrapper for Gemini (model/temp/tokens configurable).
- `agent_selector(...)`: Routes user input to one of the three agents.
- `linux_command(...)`: Parses Gemini XML, executes safe commands, returns output.
- `weather_gether(...)`: Calls WeatherAPI to return a compact forecast.
- `tech_chat(...)`: Short, technical responses.
- `FluxAIChatGUI`: Main window, chat UI, language switcher, voice toggle, Settings dialog.

---

### Desktop Integration
The installer copies the app to `/usr/share/flux-ai-chat`, creates a virtualenv under `python-env`, and writes a desktop entry to `~/.local/share/applications/Flux-AI.desktop`. Look for “Flux AI Chat” in your application menu.

To uninstall:
```bash
rm -rf /usr/share/flux-ai-chat
rm -f ~/.local/share/applications/Flux-AI.desktop
rm -rf ~/.flux_ai_chat
update-desktop-database ~/.local/share/applications || true
```

---

### Troubleshooting
- **Gemini API key not configured**: Open Settings → API Keys and add your key. Then restart the chat or the app.
- **No audio** (voice): Ensure your system audio stack is working (PipeWire/PulseAudio). Try installing/starting `pipewire-pulse` or `pulseaudio`. On some systems gTTS playback requires SDL support from `pygame`.
- **PyQt5 on Wayland**: If the UI does not show or behaves oddly, try `QT_QPA_PLATFORM=xcb python flux_ai.py`.
- **Missing system packages**: The installer attempts to install `python3`, `venv`, `libpng` headers. On other distros, install equivalents manually.
- **Weather API errors**: Verify your WeatherAPI key and internet access. The app expects a city name (e.g., “Weather in Berlin”).
- **Command execution**: Output shows stderr/stdout combined. Commands time out after 10s. Not all dangerous commands can be detected—use judgment.

---

### Security & Privacy
- Commands may be executed on your system. The deny‑list is minimal; review suggested commands before use.
- API calls are made to Google (Gemini) and WeatherAPI when those features are used.
- Configuration is stored locally at `~/.flux_ai_chat`. API keys are saved in plain JSON on your machine; protect your user account.

---

### Development
Suggestions for contributions:
- Add more agents (e.g., package management, system diagnostics).
- Extend dangerous command detection and add explicit confirmation prompts.
- Add unit tests and CI.
- Add Windows/macOS packaging (currently optimized for Linux).

Run from source with a venv (see above), then modify `flux_ai.py`. PRs and issues are welcome.

---

### License
No license provided yet. If you plan to distribute or modify, please add a suitable license file.

---

### Acknowledgements
- Google Gemini, LangChain, PyQt5, gTTS, pygame, WeatherAPI.


