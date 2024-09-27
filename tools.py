import os
import subprocess
import requests
from tqdm import tqdm
import sys

def update_path(path_var, path):
    with open(".env", "r") as f:
        lines = f.readlines()
    for line in lines:
        if path is not None:
            if path_var in line:
                lines[lines.index(line)] = f"{path_var}='{path}'\n"
    with open(".env", "w") as f:
        f.writelines(lines)

def add_path(path_var, path):
    with open(".env", "a") as f:
        if path is not None:
            f.write(f"{path_var}='{path}'\n")

def set_paths(path_var, temppath):
    if not os.path.isfile('.env'):
        try:
            with open('.env', "w") as f:
                f.write("")  # Create an empty .env file
        except Exception as e:
            print(f"An error occurred while creating the .env file: {e}")
            sys.exit(1)
    try:
        with open(".env", "r") as f:
            lines = f.read()
        if path_var in lines:
            update_path(path_var, temppath)
        else:
            add_path(path_var, temppath)
    except:
        print("An error occurred while updating the path.")
        sys.exit(1)

def run_command_out(cmd, dir=None):
    cmd = cmd.split()
    # print("Running command:", cmd)
    if dir:
        cmd[0] = dir+"/"+cmd[0]
    try:
        output = subprocess.check_output(cmd)
        return output.decode("utf-8")
    except subprocess.CalledProcessError as e:
        print("An error occurred while running the command:", e.output.decode())
        return cmd

def run_command(cmd, dir=None):
    cmd = cmd.split()
    # print("Running command:", cmd)
    if dir:
        cmd[0] = dir+"/"+cmd[0]
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError as e:
        return False
    
def download(url, fname, chunk_size=1024):
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    if os.path.isfile(fname):
        print(f"File '{fname}' already exists.")
    else:
        try:
            resp = requests.get(url, headers=headers, stream=True)
            resp.raise_for_status()  # Raise an error for bad responses
            total = int(resp.headers.get('content-length', 0))
            with open(fname, 'wb') as file, tqdm(
                desc=fname,
                total=total,
                unit='iB',
                unit_scale=True,
                unit_divisor=1024,
            ) as bar:
                for data in resp.iter_content(chunk_size=chunk_size):
                    size = file.write(data)
                    bar.update(size)
            print(f"Downloaded '{fname}' successfully.")
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
            return None
    return fname
