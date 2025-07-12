# Windows Whisper

A Windows desktop application that provides instant voice-to-text transcription using OpenAI's Whisper API with intelligent text transformation profiles.

## Features
- 🎤 Voice recording with **Ctrl+Shift** hotkey system
- 📝 Real-time waveform visualization with smooth animations
- ⚡ Instant transcription using OpenAI Whisper API
- 🔄 **5 transformation profiles** for different use cases
- 🌍 Translation support (Spanish, French)
- 💼 Professional text formatting and politeness filters
- 📋 Automatic text typing via clipboard
- 🔑 Profile switching with **Ctrl+Shift+[1-5]** hotkeys
- 🎨 Modern, non-intrusive overlay UI
- 📊 System tray integration with profile indicators

## Quick Start Guide

### 1. Get OpenAI API Key
1. Visit [OpenAI's website](https://platform.openai.com/signup)
2. Create an account or sign in
3. Go to [API Keys section](https://platform.openai.com/api-keys)
4. Click "Create new secret key"
5. Copy your API key (keep it secure!)
6. Create a file named `.env` in the application directory and add:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

### 2. Installation

#### Prerequisites
- Python 3.8 or higher ([Download Python](https://www.python.org/downloads/))
- Windows 10 or higher

#### Option 1: Simple Installation (Recommended for most users)
1. Download the latest release from the [Releases page](https://github.com/yourusername/windows-whisper/releases)
2. Extract the ZIP file to your desired location
3. Create the `.env` file with your OpenAI API key (as shown above)
4. Double-click `Windows Whisper.exe` to start

#### Option 2: From Source (For developers)
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/windows-whisper.git
   cd windows-whisper
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python main.py
   ```

### 3. Profile Configuration

The app includes 5 preconfigured transformation profiles:

1. **Profile 1**: No Transformation (raw Whisper output)
2. **Profile 2**: Polite & Professional (removes offensive language, makes text polite)
3. **Profile 3**: Translate to Spanish (with formal tone)
4. **Profile 4**: Translate to French (with formal tone)
5. **Profile 5**: Meeting Notes Style (converts to formal bullet points)

Profiles are configured in `profiles.yaml` and can be customized.

### 4. Using the Application

1. **Profile Selection & Recording**
   - Hold **Ctrl+Shift** and press **1-5** to select and start recording with that profile
   - Release **Ctrl+Shift** to stop recording
   - The system tray icon shows the current active profile number

2. **During Recording**
   - A sleek overlay appears in the top-right corner
   - Watch the real-time waveform visualization
   - See the active profile highlighted in the overlay
   - Click "×" to cancel recording

3. **Processing & Results**
   - Text is automatically transcribed using Whisper API
   - Applied transformation based on selected profile
   - Final text is automatically typed where your cursor is
   - Processing status shown in overlay (Transcribing → Transforming → Complete)

## Troubleshooting

### Common Issues

1. **API Key Issues**
   - Ensure your `.env` file is in the correct location
   - Check if the API key is valid
   - Verify you have sufficient OpenAI credits

2. **Audio Recording Issues**
   - Check if your microphone is set as the default recording device
   - Ensure no other application is using the microphone
   - Try restarting the application

3. **Profile/Hotkey Issues**
   - Profiles are switched with **Ctrl+Shift+[1-5]**, not individual keys
   - Make sure no other applications are using the same hotkey combinations
   - Check the system tray icon to see the current active profile
   - If hotkeys don't work, try running as administrator

4. **Application Won't Start**
   - Verify all dependencies are installed
   - Check if Python is in your system PATH
   - Run from command line to see error messages

### Error Messages

- `No module named 'xyz'`: Run `pip install -r requirements.txt` again
- `API key not found`: Check your `.env` file setup
- `PortAudio error`: Restart your computer or check audio devices

## Advanced Configuration

### Customizing Settings

Add to your `.env` file to modify:
- Audio recording parameters (`SAMPLE_RATE`, `MAX_RECORDING_SECONDS`)
- UI appearance settings (`UI_THEME`, `UI_OPACITY`, `OVERLAY_POSITION`, `OVERLAY_MARGIN`)

### Profile Customization

Edit `profiles.yaml` to:
- Modify existing transformation prompts
- Add new profiles (up to 5 supported)
- Change Whisper model settings
- Configure language-specific transcription
- Set up custom ChatGPT transformation prompts

### System Requirements

Minimum:
- Windows 10 (64-bit)
- 4GB RAM
- Python 3.8+
- Microphone
- Internet connection

Recommended:
- Windows 10/11 (64-bit)
- 8GB RAM
- Python 3.10+
- High-quality microphone
- Stable internet connection

## Security Notes

1. **API Key Security**
   - Never share your API key
   - Don't commit the `.env` file to version control
   - Regularly rotate your API key
   - Set usage limits in OpenAI dashboard

2. **Data Privacy**
   - Audio is processed locally before sending to OpenAI
   - Only the audio data is sent, no personal information
   - Transcribed text is stored only in clipboard
   - No data is permanently stored

## Support and Updates

- Check the [GitHub repository](https://github.com/yourusername/windows-whisper) for updates
- Submit issues for bugs or feature requests
- Join our community discussions

## License and Credits

### License

This project is licensed under the MIT License - a permissive open source license that allows for:
- ✅ Commercial use
- ✅ Modification
- ✅ Distribution
- ✅ Private use

Key points of the MIT License:
- You can freely use, modify, and distribute this software
- You must include the original copyright notice and license
- The software comes with no warranties
- The authors are not liable for any damages

See the [LICENSE](LICENSE) file for the full license text.

### Credits and Acknowledgments

This project was developed with the assistance of:

- **AI Development Support**:
  - Cursor IDE's AI pair programming features
  - Anthropic's Claude (3.5/3.7 Sonnet) for code generation and problem-solving

- **Core Technologies**:
  - [OpenAI Whisper API](https://platform.openai.com/docs/guides/speech-to-text) - Speech-to-text engine
  - [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - UI framework
  - [PyAudio](https://people.csail.mit.edu/hubert/pyaudio/) - Audio recording
  - [NumPy](https://numpy.org/) - Audio processing
  - [python-dotenv](https://github.com/theskumar/python-dotenv) - Environment management

### Contributing

Contributions are welcome! Please feel free to submit issues or pull requests. When contributing, please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

All contributions will be released under the MIT License. 