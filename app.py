import streamlit as st
import os
import shutil
import zipfile
from pathlib import Path
from compiler import compile_sketch
from patch_pipeline import firmware_patch_pipeline, sha256sum

# Directories
TEMP_DIR = "temp"
BUILD_DIR = "firmware/build"
os.makedirs(TEMP_DIR, exist_ok=True)

# Boards map
BOARD_OPTIONS = {
    "Arduino Uno": "arduino:avr:uno",
    "Arduino Nano": "arduino:avr:nano",
    "Arduino Mega 2560": "arduino:avr:mega",
    "ESP32 Dev Module": "esp32:esp32:esp32",
    "ESP8266 NodeMCU": "esp8266:esp8266:nodemcuv2"
}

def save_ino(uploaded_file, folder_name):
    sketch_dir = os.path.join(TEMP_DIR, folder_name)
    os.makedirs(sketch_dir, exist_ok=True)
    ino_path = os.path.join(sketch_dir, f"{folder_name}.ino")
    with open(ino_path, "wb") as f:
        f.write(uploaded_file.read())
    return ino_path

def zip_build_dir(build_dir, zip_file):
    with zipfile.ZipFile(zip_file, 'w') as zipf:
        for root, _, files in os.walk(build_dir):
            for file in files:
                zipf.write(os.path.join(root, file),
                           arcname=os.path.relpath(os.path.join(root, file), build_dir))

def file_size_kb(path):
    return f"{os.path.getsize(path) / 1024:.2f} KB"

# === UI ===
st.title("🔧 Arduino Delta Patch Generator")

board = st.selectbox("Select Board", list(BOARD_OPTIONS.keys()))
fqbn = BOARD_OPTIONS[board]

base_file = st.file_uploader("Upload Base .ino file", type="ino")
new_file = st.file_uploader("Upload New .ino file", type="ino")

if st.button("Generate Patch") and base_file and new_file:
    with st.spinner("Processing..."):

        # 1. Save INO files
        base_ino_path = save_ino(base_file, "base")
        new_ino_path = save_ino(new_file, "new")

        # 2. Compile
        base_sketch_path = os.path.dirname(base_ino_path)
        new_sketch_path = os.path.dirname(new_ino_path)

        base_hex = compile_sketch(base_sketch_path, fqbn, os.path.join(base_sketch_path, "build"))
        new_hex = compile_sketch(new_sketch_path, fqbn, os.path.join(new_sketch_path, "build"))

        if not base_hex or not new_hex:
            st.error("❌ Compilation failed. Check the logs.")
        else:
            os.makedirs(BUILD_DIR, exist_ok=True)
            firmware_patch_pipeline(base_hex, new_hex, BUILD_DIR)

            # Show checksum & size preview
            new_bin = os.path.join(BUILD_DIR, "new.bin")
            reconstructed_bin = os.path.join(BUILD_DIR, "reconstructed.bin")

            st.subheader("🔍 Verification Results")
            st.text(f"New   BIN checksum: {sha256sum(new_bin)} ({file_size_kb(new_bin)})")
            st.text(f"Reconstructed BIN checksum: {sha256sum(reconstructed_bin)} ({file_size_kb(reconstructed_bin)})")

            # Create ZIP
            zip_path = os.path.join("firmware", "patch_output.zip")
            zip_build_dir(BUILD_DIR, zip_path)

            # Download link
            with open(zip_path, "rb") as f:
                st.success("🎉 Patch created successfully!")
                st.download_button("📦 Download Patch ZIP", f, file_name="patch_output.zip")