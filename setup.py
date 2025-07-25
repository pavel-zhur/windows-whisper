from setuptools import setup, find_packages

setup(
    name="windows-whisper",
    version="0.4.0",
    description="A lightweight voice-to-text tool triggered by Ctrl + Space using OpenAI's Whisper API",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/windows-whisper",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "keyboard>=0.13.5",
        "pyaudio>=0.2.13",
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
        "pyperclip>=1.8.2",
        "PyQt5>=5.15.9",
        "numpy>=1.24.3",
    ],
    entry_points={
        "console_scripts": [
            "windows-whisper=main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Operating System :: Microsoft :: Windows",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
) 