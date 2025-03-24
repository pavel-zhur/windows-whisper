# 🗣️ Whisper Transcript Shortcut

A lightweight voice-to-text tool for Windows that lets you instantly transcribe speech using OpenAI's Whisper API, triggered by `Ctrl + Space`.

## ✨ Features

- **Global Hotkey**: Trigger recording from anywhere with `Ctrl + Space`
- **Modern UI**: Sleek, floating overlay with recording indicator
- **Fast Transcription**: Powered by OpenAI's Whisper API
- **Auto Clipboard**: Transcriptions automatically copied for immediate use
- **Language Support**: Multiple language transcription support
- **Configurable**: Easy configuration via environment variables
- **Distraction-Free**: Minimal interface that stays out of your way

## 🚀 Quick Start

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/windows-whisper.git
   cd windows-whisper
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up your environment:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

5. Run the application:
   ```bash
   python main.py
   ```

## 💡 Usage

1. Press `Ctrl + Space` from any application
2. Speak clearly into your microphone
3. Click "Done" when finished speaking
4. Wait for the transcription (usually takes 2-3 seconds)
5. The text is automatically copied to your clipboard
6. Paste anywhere with `Ctrl + V`

## ⚙️ Configuration

The following environment variables can be configured in `.env`:

- `OPENAI_API_KEY`: Your OpenAI API key
- `WHISPER_MODEL`: Model to use (default: "whisper-1")
- `WHISPER_LANGUAGE`: Preferred language (default: "en")
- `SHORTCUT_KEY`: Global hotkey (default: "ctrl+space")
- `MAX_RECORDING_SECONDS`: Maximum recording duration (default: 30)

## 🧪 Testing

Run the integration test to verify everything works:
```bash
python test_integration.py
```

The test will:
1. Start the application
2. Simulate recording trigger
3. Test the overlay UI
4. Verify transcription workflow

## 📋 Requirements

- Windows 10/11
- Python 3.8+
- OpenAI API key
- Microphone access

## 🔧 Troubleshooting

Common issues:

1. **Hotkey not working**: 
   - Ensure no other application is using `Ctrl + Space`
   - Try running the app as administrator

2. **Recording issues**:
   - Check your default microphone in Windows settings
   - Verify microphone permissions

3. **API errors**:
   - Verify your OpenAI API key in `.env`
   - Check your internet connection

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📄 License

MIT License - feel free to use this project however you'd like.

## 🙏 Acknowledgments

- OpenAI for the Whisper API
- PyQt5 for the UI framework
- The Python community for various helpful packages 