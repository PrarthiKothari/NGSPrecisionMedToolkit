import os
import subprocess
import sys
import time
from tools import run_command, run_command_out, set_paths
from dotenv import load_dotenv

load_dotenv()
app_dir = os.getenv("APP_DIR")
data_dir = os.getenv("DATA_DIR")

def setup_sudo(sudo_password):
    if sudo_password is None:
        print("SUDO_PASSWORD is not set in .env file.")
    else:
        try:
            commands = [ "sudo -S apt-get update"]
            for command in commands:
                try:
                    process = subprocess.Popen(command.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    output, error = process.communicate(input=(sudo_password + '\n').encode())
                    print(output.decode("utf-8"))
                    if error:
                        print("Error:", error.decode("utf-8"))
                except Exception as e:
                    print("Failed to run command:", command, "Error:", str(e))
            return True
        except Exception as e:
            print("An error occurred while setting up sudo:", str(e))
            print("Please make sure the password is correct.")
            sys.exit(1)

def setup_deps(sudo=True):
    try:
        if sudo:
            run_command_out("sudo apt-get install -y wget")
            run_command_out("sudo apt-get install -y python3-pip")
            run_command_out("sudo apt-get install -y default-jdk")
            run_command_out("sudo apt-get install -y default-jre")
            run_command_out("sudo apt-get install -y unzip")
            return True
        else:
            run_command_out("apt-get install -y wget")
            run_command_out("apt-get install -y python3-pip")
            run_command_out("apt-get install -y default-jdk")
            run_command_out("apt-get install -y default-jre")
            run_command_out("apt-get install -y unzip")
            return True
    except Exception as e:
        print("An error occurred while setting up dependencies:", str(e))
        return False

def setup_sra(app_dir):
    sra_path = f"{app_dir}/sratoolkit/bin"
    try:
        run_command_out("vdb-dump --help", dir=sra_path)
    except:
        run_command_out(f"wget -O {app_dir}/sratoolkit.tar.gz https://ftp-trace.ncbi.nlm.nih.gov/sra/sdk/3.1.1/sratoolkit.3.1.1-ubuntu64.tar.gz")
        run_command_out(f"tar -xzf {app_dir}/sratoolkit.tar.gz -C {app_dir}")
        run_command_out(f"mv {app_dir}/sratoolkit.3.1.1-ubuntu64 {app_dir}/sratoolkit")
        run_command_out(f"rm {app_dir}/sratoolkit.tar.gz")
    return sra_path

def setup_fastqc(app_dir):
    fastqc_path = f"{app_dir}/fastqc"
    try:
        run_command_out("fastqc --help", dir=fastqc_path)
    except:
        run_command_out(f"wget -O {app_dir}/fastqc.zip https://www.bioinformatics.babraham.ac.uk/projects/fastqc/fastqc_v0.12.1.zip")
        run_command_out(f"unzip {app_dir}/fastqc.zip -d {app_dir}")
        run_command_out(f"rm {app_dir}/fastqc.zip")
        run_command_out(f"mv {app_dir}/FastQC {app_dir}/fastqc-temp")
        run_command_out(f"mv {app_dir}/fastqc-temp {app_dir}/fastqc")
    return fastqc_path

def setup_fastp(app_dir):
    fastp_path = f"{app_dir}/fastp"
    os.makedirs(fastp_path, exist_ok=True)
    try:
        run_command_out("fastp --help", dir=fastp_path)
    except:
        run_command_out(f"wget -O {fastp_path}/fastp http://opengene.org/fastp/fastp")
        run_command_out(f"chmod a+x {fastp_path}/fastp")
    return fastp_path

def main(sudo_password=None):
    while sudo_password is None:
        try:
            sudo_password = os.getenv("SUDO_PASSWORD")
            if sudo_password is None:
                raise Exception("SUDO_PASSWORD is not set in .env file.")
        except:
            sudopass = input("Please enter the sudo password press Enter to continue: ")
            set_paths("SUDO_PASSWORD", sudopass.strip())
            set_paths("APP_DIR", 'applications')
            set_paths("DATA_DIR", 'data')
            print("SUDO_PASSWORD set successfully.")
            print("Please run the setup script again.")
            sys.exit(0)
    os.makedirs(app_dir, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)
    try:
        if setup_sudo(sudo_password):
            setup_deps(sudo=True)
            sra_path = setup_sra(app_dir)
            set_paths("SRATOOLKIT_PATH", sra_path)
            fastqc_path = setup_fastqc(app_dir)
            set_paths("FASTQC_PATH", fastqc_path)
            fastp_path = setup_fastp(app_dir)
            set_paths("FASTP_PATH", fastp_path)
            print("Setup completed successfully.")
        else:
            setup_deps(sudo=False)
            sra_path = setup_sra(app_dir)
            set_paths("SRATOOLKIT_PATH", sra_path)
            fastqc_path = setup_fastqc(app_dir)
            set_paths("FASTQC_PATH", fastqc_path)
            fastp_path = setup_fastp(app_dir)
            set_paths("FASTP_PATH", fastp_path)
            print("Setup completed successfully.")
    except:
        print("An error occurred while setting up system.")

if __name__ == "__main__":
    system_os = sys.platform
    if system_os != 'linux':
        print("This application is specifically built for Linux systems.")
        print("Please install WSL on Windows or use VirtualBox to run this application.")
        for i in range(30):
            print("Closing application in", 30-i, "seconds...", end="\r")
            time.sleep(1)
        sys.exit(1)
    main()