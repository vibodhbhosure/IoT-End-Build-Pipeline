# app.py
import streamlit as st
import os
import io
import zipfile
import time
from compiler import compile_sketch
from patch_pipeline import firmware_patch_pipeline, sha256sum
from utils import generate_unique_id, file_size_kb
from db_utils import save_firmware_entry, get_firmware_options, load_firmware_db

# === Constants ===
COMPILED_DIR = "compiled"
BUILD_DIR = "firmware/build"
TEMP_DIR = "temp"
DUMMY_HEX = ":10000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00\n:00000001FF\n"

os.makedirs(COMPILED_DIR, exist_ok=True)
os.makedirs(BUILD_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

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

# === UI ===
st.set_page_config()
tabs = st.tabs(["🔧 Generate Patch", "📊 Firmware Analysis"])

with tabs[0]:
    st.title("🛠️ Arduino Patch Generator with Compilation History")

    board = st.selectbox("Select Board", list(BOARD_OPTIONS.keys()))
    fqbn = BOARD_OPTIONS[board]

    st.subheader("🕹️ Step 1: Select base firmware (from previous compilations)")
    firmware_list = get_firmware_options()
    base_options = [x[0] for x in firmware_list]
    no_firmware = len(firmware_list) == 0

    base_choice = st.selectbox(
        "Choose compiled firmware",
        options=base_options if not no_firmware else ["<No compiled firmware found – use blank>"]
    )

    base_hex = dict(firmware_list).get(base_choice, None)

    # Create dummy.hex if nothing is selected
    if not base_hex:
        blank_hex_path = os.path.join(TEMP_DIR, "blank.hex")
        with open(blank_hex_path, "w") as f:
            f.write(DUMMY_HEX)
        base_hex = blank_hex_path

    st.subheader("🆕 Step 2: Upload new firmware (.ino) to compare & patch")
    new_file = st.file_uploader("Upload .ino file", type="ino")

    if st.button("Compile and Generate Patch") and base_hex and new_file:
        with st.spinner("Processing..."):
            sketch_hash = generate_unique_id()
            new_ino_path = save_ino(new_file, sketch_hash)
            sketch_path = os.path.dirname(new_ino_path)

            # Compile and store
            hex_output_path = os.path.join(COMPILED_DIR, sketch_hash)
            os.makedirs(hex_output_path, exist_ok=True)
            new_hex = compile_sketch(sketch_path, fqbn, hex_output_path)

            if not new_hex or not os.path.exists(base_hex):
                st.error("Compilation failed or base firmware not found.")
            else:
                save_firmware_entry({
                    "hash": sketch_hash,
                    "label": new_file.name,
                    "board": board,
                    "date": generate_unique_id(timestamp_only=True),
                    "hex_path": new_hex
                })

                firmware_patch_pipeline(base_hex, new_hex, BUILD_DIR)
                # Save patch.bin to compiled/<hash>/patch.bin
                patch_src = os.path.join(BUILD_DIR, "patch.bin")
                patch_dst = os.path.join(hex_output_path, "patch.bin")
                if os.path.exists(patch_src):
                    import shutil
                    shutil.copy(patch_src, patch_dst)

                new_bin = os.path.join(BUILD_DIR, "new.bin")
                reconstructed_bin = os.path.join(BUILD_DIR, "reconstructed.bin")

                st.subheader("✅ Verification")
                st.text(f"New BIN: {sha256sum(new_bin)} ({file_size_kb(new_bin)})")
                st.text(f"Reconstructed BIN: {sha256sum(reconstructed_bin)} ({file_size_kb(reconstructed_bin)})")

                zip_path = os.path.join("firmware", "patch_output.zip")
                zip_build_dir(BUILD_DIR, zip_path)

                with open(zip_path, "rb") as f:
                    st.download_button("📦 Download Patch Output ZIP", f, file_name="patch_output.zip")

with tabs[1]:
    st.title("📊 Firmware Build Analysis")

    db = load_firmware_db()
    if not db:
        st.info("No firmware builds found.")
    else:
        # Search bar
        query = st.text_input("🔍 Search firmware by label or hash")
        
        # Sort options
        col1, col2 = st.columns(2)
        sort_by = col1.selectbox("Sort by", ["Date", "Label", "Size"])
        sort_order = col2.radio("Order", ["Descending", "Ascending"], horizontal=True)

        # Prepare data rows
        rows = []
        for entry in db:
            hex_path = entry["hex_path"]
            folder = os.path.dirname(hex_path)
            if not os.path.exists(hex_path):
                continue

            row = {
                "Label": entry["label"],
                "Hash": entry["hash"],
                "Board": entry["board"],
                "Date": entry["date"],
                "Size": file_size_kb(hex_path),
                "SHA-256": sha256sum(hex_path),
                "HEX Path": hex_path,
                "Folder": folder,
            }
            if query.lower() in row["Label"].lower() or query.lower() in row["Hash"].lower():
                rows.append(row)

        # Sort logic
        reverse = sort_order == "Descending"
        key_map = {
            "Date": lambda x: x["Date"],
            "Label": lambda x: x["Label"].lower(),
            "Size": lambda x: float(x["Size"].split()[0])
        }
        rows = sorted(rows, key=key_map[sort_by], reverse=reverse)

        # Display
        for row in rows:
            st.markdown("### 🧱 Firmware: " + row["Label"])
            c1, c2, c3, c4 = st.columns(4)
            c1.write(f"📁 **Hash:** {row['Hash']}")
            c2.write(f"📅 **Date:** {row['Date']}")
            c3.write(f"📦 **Size:** {row['Size']}")
            c4.write(f"🔐 **SHA-256:** {row['SHA-256']}")

            # Create zip to download
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(row["Folder"]):
                    for file in files:
                        path = os.path.join(root, file)
                        zipf.write(path, os.path.relpath(path, row["Folder"]))
            zip_buffer.seek(0)

            st.download_button(
                label="⬇️ Download All Files",
                data=zip_buffer,
                file_name=f"{row['Hash']}_firmware.zip",
                mime="application/zip"
            )

            st.divider()