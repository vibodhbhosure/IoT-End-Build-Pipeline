import subprocess
import os
from logger import logger

arduino_cli_path = "arduino-cli"

def compile_sketch(sketch_path, fqbn, build_path):
    try:
        logger.info(f"Compiling sketch at: {sketch_path}")
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
            logger.info("✅ Compilation successful!")
            # Rename *.hex to match <build_folder>.hex
            for file in os.listdir(build_path):
                if file.endswith(".hex"):
                    original = os.path.join(build_path, file)
                    final = os.path.join(build_path, os.path.basename(build_path) + ".hex")
                    os.rename(original, final)
                    logger.info(f"👉 Compiled sketch renamed to: {final}")
                    return final
            logger.warning("⚠️ HEX file not found in build directory.")
        else:
            logger.error("❌ Compilation failed!")
            logger.error(result.stderr)
    except FileNotFoundError:
        logger.error("🚫 Arduino CLI not found. Make sure it's installed and in your PATH.")