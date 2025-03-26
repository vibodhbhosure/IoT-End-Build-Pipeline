import hashlib
import time
import os

def generate_unique_id(timestamp_only=False):
    timestamp = str(int(time.time()))
    if timestamp_only:
        return time.strftime("%d %b %Y, %H:%M:%S", time.localtime())
    salt = os.urandom(8)
    return hashlib.sha256((timestamp + str(salt)).encode()).hexdigest()[:12]

def save_metadata(path, data: dict):
    with open(path, 'w') as f:
        for key, value in data.items():
            f.write(f"{key}:{value}\n")

def read_metadata(path):
    data = {}
    with open(path, 'r') as f:
        for line in f:
            if ':' in line:
                k, v = line.strip().split(':', 1)
                data[k.strip()] = v.strip()
    return data