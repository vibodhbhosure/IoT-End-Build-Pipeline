import os
import subprocess
import hashlib
from pathlib import Path

# CONFIG
AVR_OBJCOPY = "avr-objcopy"  # Make sure it's in PATH
BSDIFF = "bsdiff"
BSPATCH = "bspatch"

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def run_cmd(cmd, check=True):
    print(f"🚀 Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=check)

def convert_hex_to_bin(hex_file, bin_file):
    run_cmd([AVR_OBJCOPY, "-I", "ihex", "-O", "binary", hex_file, bin_file])
    print(f"✅ Converted HEX ➝ BIN: {bin_file}")

def convert_bin_to_hex(bin_file, hex_file):
    run_cmd([AVR_OBJCOPY, "-I", "binary", "-O", "ihex", bin_file, hex_file])
    print(f"✅ Converted BIN ➝ HEX: {hex_file}")

def create_patch(base_bin, new_bin, patch_file):
    run_cmd([BSDIFF, base_bin, new_bin, patch_file])
    print(f"✅ Patch created: {patch_file}")

def apply_patch(base_bin, reconstructed_bin, patch_file):
    run_cmd([BSPATCH, base_bin, reconstructed_bin, patch_file])
    print(f"✅ Patch applied: {reconstructed_bin}")

def sha256sum(file_path):
    with open(file_path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def verify_reconstruction(new_bin, reconstructed_bin):
    hash1 = sha256sum(new_bin)
    hash2 = sha256sum(reconstructed_bin)
    if hash1 == hash2:
        print("✅ Verification successful: Reconstructed firmware matches the new firmware.")
    else:
        print("❌ Verification failed: Hash mismatch.")
        print(f"Expected: {hash1}")
        print(f"Got     : {hash2}")

# === MAIN PIPELINE ===
def firmware_patch_pipeline(base_hex, new_hex, build_dir):
    ensure_dir(build_dir)

    # Output files
    base_bin = os.path.join(build_dir, "base.bin")
    new_bin = os.path.join(build_dir, "new.bin")
    patch_file = os.path.join(build_dir, "patch.bin")
    reconstructed_bin = os.path.join(build_dir, "reconstructed.bin")
    reconstructed_hex = os.path.join(build_dir, "reconstructed.hex")

    # Step 1: Convert HEX to BIN
    convert_hex_to_bin(base_hex, base_bin)
    convert_hex_to_bin(new_hex, new_bin)

    # Step 2: Generate patch
    create_patch(base_bin, new_bin, patch_file)

    # Step 3: Apply patch
    apply_patch(base_bin, reconstructed_bin, patch_file)

    # Step 4: Convert reconstructed BIN back to HEX (optional)
    convert_bin_to_hex(reconstructed_bin, reconstructed_hex)

    # Step 5: Verify patching
    verify_reconstruction(new_bin, reconstructed_bin)

# === USAGE ===
if __name__ == "__main__":
    base_hex = "sketch/blink/build/blink.ino.hex"
    new_hex = "sketch/fast-blink/build/fast-blink.ino.hex"
    build_dir = "firmware/build"
    
    firmware_patch_pipeline(base_hex, new_hex, build_dir)