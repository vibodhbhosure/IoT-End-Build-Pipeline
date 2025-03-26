import subprocess
import os

# === CONFIGURATION ===
arduino_cli_path = "arduino-cli"
board_fqbn = "arduino:avr:uno"  # Change based on your board
ino_file_path = "sketch/fast-blink/fast-blink.ino"  # Full path to the .ino file

# Extract the folder containing the .ino file
sketch_path = os.path.dirname(os.path.abspath(ino_file_path))
build_path = os.path.join(sketch_path, "build")

def compile_sketch(sketch_path, fqbn, build_path):
    try:
        print(f"Compiling sketch at: {sketch_path}")
        os.makedirs(build_path, exist_ok=True)

        result = subprocess.run(
            [
                arduino_cli_path, "compile",
                "--fqbn", fqbn,
                "--output-dir", build_path,
                sketch_path
            ],
            capture_output=True, text=True
        )

        if result.returncode == 0:
            print("✅ Compilation successful!")
            for file in os.listdir(build_path):
                if file.endswith(".hex") or file.endswith(".bin"):
                    hex_path = os.path.join(build_path, file)
                    print(f"👉 Compiled sketch located at: {hex_path}")
                    return hex_path
            print("⚠️ Compiled file not found in output directory.")
        else:
            print("❌ Compilation failed!")
            print(result.stderr)
    except FileNotFoundError:
        print("🚫 Arduino CLI not found. Check your installation and PATH.")

# === RUN ===
compile_sketch(sketch_path, board_fqbn, build_path)