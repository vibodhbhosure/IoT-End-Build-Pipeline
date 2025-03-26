# 🔧 Arduino Delta Patch Generator

A Streamlit app that:
- Compiles two Arduino `.ino` files (base + new)
- Generates a binary delta patch using `bsdiff`
- Verifies output with checksum and size comparison
- Downloads all artifacts in a `.zip` file

## 🧰 Features
- Board selection: Uno, Nano, Mega, ESP32, ESP8266
- Checksum verification (SHA-256)
- File size comparison
- Downloadable ZIP of `bin`, `hex`, and `patch.bin`

## 📦 Installation

```bash
git clone https://github.com/yourname/arduino-patch-generator
cd arduino-patch-generator
pip install -r requirements.txt