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

def setup_bwa(app_dir):
    bwa_path = f"{app_dir}/bwa"
    #os.makedirs(bwa_path, exist_ok=True)
    try:
        run_command_out("{app_dir}/bwa", dir=bwa_path)
    except:
        run_command_out(f"wget -O {app_dir}/bwa.tar.bz2 https://sourceforge.net/projects/bio-bwa/files/bwa-0.7.17.tar.bz2/download")
        run_command_out(f"tar -xjf {app_dir}/bwa.tar.bz2 -C {app_dir}")
        run_command_out(f"rm -rf {app_dir}/bwa.tar.bz2")
        run_command_out(f"mv {app_dir}/bwa-0.7.17 {app_dir}/bwa")
        run_command_out(f"make -C {app_dir}/bwa") 
    return bwa_path

def setup_docker(app_dir):
    """Sets up Docker in the specified application directory."""
    docker_path = f"{app_dir}/docker"
    os.makedirs(docker_path, exist_ok=True)

    # Try to run a simple Docker command to check if Docker is installed.
    try:
        run_command_out("docker -V")
        print("Docker is already installed.")

    except Exception as e:
        print("Docker is not installed. Proceeding with installation...")

        # Install prerequisites
        run_command_out("sudo apt-get update")
        run_command_out("sudo apt-get install -y ca-certificates curl")
        run_command_out("sudo install -m 0755 -d /etc/apt/keyrings")
        
        # Add Docker's official GPG key
        run_command_out("sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc")
        run_command_out("sudo chmod a+r /etc/apt/keyrings/docker.asc")

        # Get architecture
        arch = subprocess.check_output("dpkg --print-architecture", shell=True).decode().strip()

        # Get Ubuntu codename
        codename = subprocess.check_output("lsb_release -cs", shell=True).decode().strip()

        # Create Docker source list entry
        docker_source = f'deb [arch={arch} signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu {codename} stable'
        subprocess.run(f'echo "{docker_source}" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null', shell=True, check=True)
        
        run_command_out("sudo apt-get update -y")

        # Install Docker
        run_command_out("sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin")

        # Start and enable Docker service
        run_command_out("sudo systemctl start docker")
        run_command_out("sudo systemctl enable docker")

        # Check status of Docker service
        run_command_out("sudo systemctl status docker")

    return docker_path

# def setup_gatk(app_dir):
#     gatk_path = f"{app_dir}/gatk"
#     os.makedirs(gatk_path, exist_ok=True)
#     try:
#         run_command_out("gatk --help", dir=gatk_path)
#     except:
#         run_command_out(f"wget -O {gatk_path}/gatk.zip")

# def setup_bcftools(app_dir):
#     bcftools_path = f"{app_dir}/bcftools"
#     os.makedirs(bcftools_path, exist_ok=True)
#     try:
#         run_command_out("bcftools --help", dir=bcftools_path)
#     except:
#         run_command_out(f"wget -O {bcftools_path}/bcftools.tar.bz2")

# def setup_samtools(app_dir):
#     samtools_path = f"{app_dir}/samtools"
#     os.makedirs(samtools_path, exist_ok=True)
#     try:
#         run_command_out("samtools --help", dir=samtools_path)
#     except:
#         run_command_out(f"wget -O {samtools_path}/samtools.tar.bz2")


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
            bwa_path = setup_bwa(app_dir)
            set_paths("BWA_PATH", bwa_path)
            docker_path = setup_docker(app_dir)
            set_paths("DOCKER_PATH", docker_path)
            print(f"Docker has been set up at: {docker_path}")

            # GATK
            #gatk_path = setup_gatk(app_dir)
            #set_paths("GATK_PATH", gatk_path)

            # BCFTOOLS
            #bcftools_path = setup_bcftools(app_dir)
            #set_paths("BCFTOOLS_PATH", bcftools_path)

            # SAMTOOLS
            #samtools_path = setup_samtools(app_dir)
            #set_paths("SAMTOOLS_PATH", samtools_path)

            print("Setup completed successfully.")
        else:
            setup_deps(sudo=False)
            sra_path = setup_sra(app_dir)
            set_paths("SRATOOLKIT_PATH", sra_path)
            fastqc_path = setup_fastqc(app_dir)
            set_paths("FASTQC_PATH", fastqc_path)
            fastp_path = setup_fastp(app_dir)
            set_paths("FASTP_PATH", fastp_path)
            bwa_path = setup_bwa(app_dir)
            set_paths("BWA_PATH", bwa_path)
            docker_path = setup_docker(app_dir)
            set_paths("DOCKER_PATH", docker_path)
            print(f"Docker has been set up at: {docker_path}")

            # GATK
            #gatk_path = setup_gatk(app_dir)
            #set_paths("GATK_PATH", gatk_path)

            # BCFTOOLS
            #bcftools_path = setup_bcftools(app_dir)
            #set_paths("BCFTOOLS_PATH", bcftools_path)

            # SAMTOOLS
            #samtools_path = setup_samtools(app_dir)
            #set_paths("SAMTOOLS_PATH", samtools_path)

            print("Setup completed successfully.")
    except Exception as e:
        print(e)

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