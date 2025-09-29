#!/usr/bin/env python3
"""Setup script for RelayShell."""

from setuptools import setup, find_packages

setup(
    name="relayshell",
    version="1.0.0",
    description="AI-powered development assistant with Tamil/English speech support",
    author="RelayShell Team",
    author_email="admin@relayshell.dev",
    packages=find_packages(),
    install_requires=[
        "pyyaml>=6.0",
        "requests>=2.31.0",
        "aiohttp>=3.8.0",
        "speechrecognition>=3.10.0",
        "pyttsx3>=2.90",
        "pyaudio>=0.2.11",
        "pyperclip>=1.8.2",
        "psutil>=5.9.0",
        "pexpect>=4.8.0",
        "langdetect>=1.0.9",
        "googletrans>=4.0.0",
        "jsonschema>=4.17.0",
        "pydantic>=2.0.0",
        "colorlog>=6.7.0",
        "click>=8.1.0",
        "openai>=1.0.0",
        "anthropic>=0.3.0",
        "google-generativeai>=0.3.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "relayshell=relayshell.cli:main",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)