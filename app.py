import os
import sys
import subprocess
import requests
from tqdm import tqdm
import shutil
import time
import tarfile
import gradio as gr
from dotenv import load_dotenv

# ------------------ HELPER FUNCTIONS ------------------
def update_path(path_var, path):
    with open(".env", "r") as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        if path is not None and path_var in line:
            lines[i] = f"{path_var}='{path}'\n"
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
                f.write("")
        except Exception as e:
            print(f"Error creating .env file: {e}")
            sys.exit(1)
    try:
        with open(".env", "r") as f:
            content = f.read()
        if path_var in content:
            update_path(path_var, temppath)
        else:
            add_path(path_var, temppath)
    except Exception as e:
        print("Error updating path:", e)
        sys.exit(1)

def run_command_out(cmd, dir=None):
    cmd_list = cmd.split()
    if dir is not None:
        # If the command is not an absolute path, prepend the directory.
        if not os.path.isabs(cmd_list[0]):
            cmd_list[0] = os.path.join(dir, cmd_list[0])
    try:
        output = subprocess.check_output(cmd_list)
        return output.decode("utf-8")
    except subprocess.CalledProcessError as e:
        print("Error running command:", e.output.decode())
        return cmd

def run_command(cmd, dir=None):
    cmd_list = cmd.split()
    if dir is not None:
        if not os.path.isabs(cmd_list[0]):
            cmd_list[0] = os.path.join(dir, cmd_list[0])
    try:
        subprocess.run(cmd_list, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
            resp.raise_for_status()
            total = int(resp.headers.get('content-length', 0))
            with open(fname, 'wb') as file, tqdm(desc=fname, total=total, unit='iB', unit_scale=True, unit_divisor=1024) as bar:
                for data in resp.iter_content(chunk_size=chunk_size):
                    size = file.write(data)
                    bar.update(size)
            print(f"Downloaded '{fname}' successfully.")
        except requests.exceptions.RequestException as e:
            print(f"Download error: {e}")
            return None
    return fname

# ------------------ INSTALL SRA TOOLKIT ------------------
def install_sra():
    print("SRA Toolkit not found. Downloading now...")
    fname = "sratoolkit.tar.gz"
    file = download(url="https://ftp-trace.ncbi.nlm.nih.gov/sra/sdk/3.1.1/sratoolkit.3.1.1-ubuntu64.tar.gz", fname=fname)
    if not file:
        print("Download failed.")
        return
    print("SRA Toolkit downloaded.")
    with tarfile.open(file, "r:gz") as tar:
        tar.extractall()
    print("SRA Toolkit extracted.")
    extracted_dir = "sratoolkit.3.1.1-ubuntu64"
    os.remove(fname)
    if os.path.exists(extracted_dir):
        os.rename(extracted_dir, "sratoolkit")
        print("SRA Toolkit installed.")
    else:
        print(f"Error: '{extracted_dir}' not found after extraction.")

# ------------------ LOAD ENVIRONMENT VARIABLES ------------------
load_dotenv()
app_dir = os.getenv("APP_DIR", "applications")
data_dir = os.getenv("DATA_DIR", "data")
sratoolkit_path = os.getenv("SRATOOLKIT_PATH")
fastqc_path = os.getenv("FASTQC_PATH")
fastp_path = os.getenv("FASTP_PATH")

# ------------------ SETUP FUNCTIONS ------------------
def setup_sudo(sudo_password):
    if sudo_password is None:
        return "SUDO_PASSWORD is not set in .env file."
    try:
        commands = ["sudo -S apt-get update"]
        output_log = ""
        for command in commands:
            proc = subprocess.Popen(command.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, error = proc.communicate(input=(sudo_password + '\n').encode())
            output_log += output.decode("utf-8")
            if error:
                output_log += "Error: " + error.decode("utf-8") + "\n"
        return output_log
    except Exception as e:
        return f"Error setting up sudo: {e}"

def setup_deps(sudo=True):
    try:
        if sudo:
            run_command_out("sudo apt-get install -y wget")
            run_command_out("sudo apt-get install -y python3-pip")
            run_command_out("sudo apt-get install -y default-jdk")
            run_command_out("sudo apt-get install -y default-jre")
            run_command_out("sudo apt-get install -y unzip")
            run_command_out("sudo apt-get install -y build-essential")
            run_command_out("sudo apt-get install -y bwa")
            run_command_out("gcc --version")
            run_command_out("sudo apt-get install -y zlib1g-dev")
            return "Dependencies installed with sudo."
        else:
            run_command_out("apt-get install -y wget")
            run_command_out("apt-get install -y python3-pip")
            run_command_out("apt-get install -y default-jdk")
            run_command_out("apt-get install -y default-jre")
            run_command_out("apt-get install -y unzip")
            run_command_out("apt-get install -y build-essential")
            run_command_out("apt-get install -y bwa")
            run_command_out("gcc --version")
            run_command_out("apt-get install -y zlib1g-dev")
            return "Dependencies installed without sudo."
    except Exception as e:
        return f"Error installing dependencies: {e}"

def setup_sra(app_dir):
    sra_path_local = f"{app_dir}/sratoolkit/bin"
    try:
        run_command_out("vdb-dump --help", dir=sra_path_local)
    except Exception:
        run_command_out(f"wget -O {app_dir}/sratoolkit.tar.gz https://ftp-trace.ncbi.nlm.nih.gov/sra/sdk/3.1.1/sratoolkit.3.1.1-ubuntu64.tar.gz")
        run_command_out(f"tar -xzf {app_dir}/sratoolkit.tar.gz -C {app_dir}")
        run_command_out(f"mv {app_dir}/sratoolkit.3.1.1-ubuntu64 {app_dir}/sratoolkit")
        run_command_out(f"rm {app_dir}/sratoolkit.tar.gz")
    return f"{app_dir}/sratoolkit/bin"

def setup_fastqc(app_dir):
    fastqc_path_local = f"{app_dir}/fastqc"
    try:
        run_command_out("fastqc --help", dir=fastqc_path_local)
    except Exception:
        run_command_out(f"wget -O {app_dir}/fastqc.zip https://www.bioinformatics.babraham.ac.uk/projects/fastqc/fastqc_v0.12.1.zip")
        run_command_out(f"unzip {app_dir}/fastqc.zip -d {app_dir}")
        run_command_out(f"rm {app_dir}/fastqc.zip")
        run_command_out(f"mv {app_dir}/FastQC {app_dir}/fastqc-temp")
        run_command_out(f"mv {app_dir}/fastqc-temp {app_dir}/fastqc")
    return f"{app_dir}/fastqc"

def setup_fastp(app_dir):
    fastp_path_local = f"{app_dir}/fastp"
    os.makedirs(fastp_path_local, exist_ok=True)
    try:
        run_command_out("fastp --help", dir=fastp_path_local)
    except Exception:
        run_command_out(f"wget -O {fastp_path_local}/fastp http://opengene.org/fastp/fastp")
        run_command_out(f"chmod a+x {fastp_path_local}/fastp")
    return fastp_path_local

def run_setup(sudo_password):
    os.makedirs(app_dir, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)
    log = ""
    log += setup_sudo(sudo_password) + "\n"
    log += setup_deps(sudo=True) + "\n"
    sra_p = setup_sra(app_dir)
    set_paths("SRATOOLKIT_PATH", sra_p)
    global sratoolkit_path
    sratoolkit_path = sra_p  # update global variable
    log += f"Set SRA Toolkit path: {sra_p}\n"
    fastqc_p = setup_fastqc(app_dir)
    set_paths("FASTQC_PATH", fastqc_p)
    log += f"Set FastQC path: {fastqc_p}\n"
    fastp_p = setup_fastp(app_dir)
    set_paths("FASTP_PATH", fastp_p)
    log += f"Set Fastp path: {fastp_p}\n"
    log += "Setup completed successfully."
    return log

# ------------------ SRA TOOLKIT INTEGRATION ------------------
def sra_cmd_for_info(accession: str):
    toolkit_path = os.getenv("SRATOOLKIT_PATH") or f"{app_dir}/sratoolkit/bin"
    vdb_dump_path = os.path.join(toolkit_path, "vdb-dump")
    return f"{vdb_dump_path} {accession} --info"

def sra_cmd_to_download(accession: str,
                        alignment_filter: bool,
                        compressed: bool,
                        skip_technical: bool,
                        remove_adapter: bool,
                        spot_group: bool,
                        alignment_filter_type: str = None,
                        min_reads: int = None,
                        max_reads: int = None,
                        ar_specific: str = None,
                        ar_start: int = None,
                        ar_end: int = None,
                        member: str = None):
    toolkit_path = os.getenv("SRATOOLKIT_PATH") or f"{app_dir}/sratoolkit/bin"
    fastq_dump_path = os.path.join(toolkit_path, "fastq-dump")
    cmd_list = [fastq_dump_path, accession, '--split-3', '--outdir', f'{data_dir}/{accession}']
    if compressed:
        cmd_list.append('--gzip')
    if alignment_filter:
        if alignment_filter_type == "split-spot":
            if '--split-3' in cmd_list: cmd_list.remove('--split-3')
            cmd_list.append('--split-spot')
        elif alignment_filter_type == "aligned":
            if '--split-3' in cmd_list: cmd_list.remove('--split-3')
            cmd_list.append('--aligned')
        elif alignment_filter_type == "unaligned":
            if '--split-3' in cmd_list: cmd_list.remove('--split-3')
            cmd_list.append('--unaligned')
        elif alignment_filter_type == "aligned-region":
            if '--split-3' in cmd_list: cmd_list.remove('--split-3')
            cmd_list.append('--aligned-region')
            cmd_list.append(f'{ar_specific}:{ar_start}-{ar_end}')
        elif alignment_filter_type == "matepair-distance":
            if '--split-3' in cmd_list: cmd_list.remove('--split-3')
            cmd_list.append('--matepair-distance')
            cmd_list.append(f'{ar_start}-{ar_end}')
    if skip_technical:
        cmd_list.append('--skip-technical')
    if min_reads:
        cmd_list.extend(['--minSpotId', str(min_reads)])
    if max_reads:
        cmd_list.extend(['--maxSpotId', str(max_reads)])
    if remove_adapter:
        cmd_list.append('--clip')
    if spot_group:
        cmd_list.extend(['--spot-group', member])
    return ' '.join(cmd_list)

def list_files_in_directory(directory):
    try:
        return [os.path.join(directory, f) for f in os.listdir(directory)
                if os.path.isfile(os.path.join(directory, f))]
    except Exception as e:
        return []

def compress_dir(directory, zip_filename):
    import zipfile
    with zipfile.ZipFile(zip_filename, mode='w') as zip_file:
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                zip_file.write(file_path, arcname=os.path.relpath(file_path, directory))
    return zip_filename

def sra_download_main(accession: str,
                      alignment_filter_type: str,
                      alignment_filter: bool,
                      compressed: bool,
                      skip_technical: bool,
                      remove_adapter: bool,
                      spot_group: bool,
                      min_reads: int = None,
                      max_reads: int = None,
                      ar_specific: str = None,
                      ar_start: int = None,
                      ar_end: int = None,
                      member: str = None):
    try:
        shutil.rmtree(data_dir)
    except FileNotFoundError:
        print("Data folder not found; proceeding.")
    except OSError as e:
        print("Error removing data folder:", e)
    sra_info_cmd = sra_cmd_for_info(accession)
    try:
        run_command_out(sra_info_cmd)
    except Exception as e:
        try:
            install_sra()
        except Exception as e:
            print("Error during SRA installation:", e)
    work_dir = os.path.join(data_dir, accession)
    os.makedirs(work_dir, mode=0o777, exist_ok=True)
    # Set the working directory environment variable for downstream steps
    os.environ["WORKING_DIR"] = work_dir
    get_data_cmd = sra_cmd_for_info(accession)
    download_cmd = sra_cmd_to_download(accession, alignment_filter, compressed,
                                       skip_technical, remove_adapter, spot_group,
                                       alignment_filter_type, min_reads, max_reads,
                                       ar_specific, ar_start, ar_end, member)
    log = f"Fetching data with: {get_data_cmd}\n"
    data_info = run_command_out(get_data_cmd)
    log += f"Data info: {data_info}\n"
    log += f"Downloading Fastq files with: {download_cmd}\n"
    download_status = run_command_out(download_cmd)
    log += f"Download status: {download_status}\n"
    zip_file = compress_dir(work_dir, os.path.join(data_dir, f"{accession}.zip"))
    print(f"Data downloaded successfully for {accession}")
    return data_info, download_status, zip_file

# ------------------ FASTQC INTEGRATION ------------------
def fastqc_main(uploaded_files):
    working_dir = os.getenv("WORKING_DIR")
    if not working_dir:
        return "Working directory not set. Run the SRA download step first.", []
    # Copy uploaded files into working directory
    for file_obj in uploaded_files:
        dest = os.path.join(working_dir, os.path.basename(file_obj.name))
        shutil.copy(file_obj.name, dest)
        print(f"Copied {file_obj.name} to {dest}")  # Debug print
    output_dir = os.path.join(working_dir, 'fastqc_reports')
    os.makedirs(output_dir, exist_ok=True)
    # Process each file with FastQC
    for f in os.listdir(working_dir):
        file_path = os.path.join(working_dir, f)
        if any(ext in f for ext in [".fastq", ".fasta", ".fa", ".sam", ".bam"]):
            cmd = f"fastqc {file_path} --outdir {output_dir}"
            print(f"Running FastQC command: {cmd}")  # Debug print
            try:
                # Use fastqc_path as the directory where the fastqc binary is located
                run_command_out(cmd, dir=fastqc_path)
            except Exception as e:
                print(f"Error running FastQC on {file_path}: {e}")
    # Collect reports (HTML files)
    reports = [os.path.join(output_dir, f) for f in os.listdir(output_dir)
               if f.endswith(".html")]
    if not reports:
        print("No FastQC reports were generated.")
    else:
        print("Generated FastQC reports:", reports)
    return "FastQC processing completed.", reports

# ------------------ FASTP INTEGRATION ------------------
def fastp_main(uploaded_files):
    working_dir = os.getenv("WORKING_DIR")
    if not working_dir:
        return "Working directory not set. Run the SRA download step first.", []
    if len(uploaded_files) < 2:
        return "Please upload two FASTQ files (forward and reverse).", []
    file1, file2 = uploaded_files[0], uploaded_files[1]
    dest1 = os.path.join(working_dir, os.path.basename(file1.name))
    dest2 = os.path.join(working_dir, os.path.basename(file2.name))
    shutil.copy(file1.name, dest1)
    shutil.copy(file2.name, dest2)
    output_file_1 = os.path.join(working_dir, os.path.basename(dest1).replace('.fastq.gz', '_trimmed.fastq.gz'))
    output_file_2 = os.path.join(working_dir, os.path.basename(dest2).replace('.fastq.gz', '_trimmed.fastq.gz'))
    output_dir = os.path.join(working_dir, 'fastp_reports')
    os.makedirs(output_dir, exist_ok=True)
    command = (f"{fastp_path}/fastp"
               f" -i {dest1}"
               f" -o {output_file_1}"
               f" -I {dest2}"
               f" -O {output_file_2}"
               f" --detect_adapter_for_pe"
               f" -f 10 -g -l 50"
               f" -c -h {output_dir}/fastp_report.html"
               f" -w 10")
    try:
        run_command_out(command)
        trimmed_dir = os.path.join(working_dir, 'trimmed')
        os.makedirs(trimmed_dir, exist_ok=True)
        shutil.move(output_file_1, os.path.join(trimmed_dir, os.path.basename(output_file_1)))
        shutil.move(output_file_2, os.path.join(trimmed_dir, os.path.basename(output_file_2)))
        trimmed_files = [os.path.join(trimmed_dir, os.path.basename(output_file_1)),
                         os.path.join(trimmed_dir, os.path.basename(output_file_2))]
        return "Fastp processing completed.", trimmed_files
    except Exception as e:
        return f"Error running Fastp: {e}", []

# ------------------ UI HELPER FUNCTIONS ------------------
def enable_spot_group(esg):
    return gr.update(visible=True) if esg else gr.update(visible=False)

def enable_reads_count(erc):
    return (gr.update(visible=True), gr.update(visible=True)) if erc else (gr.update(visible=False), gr.update(visible=False))

def enable_alignment_filter(eaf):
    return gr.update(visible=True) if eaf else gr.update(visible=False)

def enable_alignment_filter_type(eaft):
    if eaft == "aligned-region":
        return gr.update(visible=True), gr.update(visible=True), gr.update(visible=True)
    elif eaft == "matepair-distance":
        return gr.update(visible=False), gr.update(visible=True), gr.update(visible=True)
    else:
        return gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)

def get_fastq(accession, alignment_filter_type, alignment_filter, compression,
              skip_technical, remove_adapter, spot_group, min_reads, max_reads,
              ar_specific, ar_start, ar_end, member):
    print("Received parameters:")
    print("accession:", accession)
    print("alignment_filter_type:", alignment_filter_type)
    print("alignment_filter:", alignment_filter)
    print("compression:", compression)
    print("skip_technical:", skip_technical)
    print("remove_adapter:", remove_adapter)
    print("spot_group:", spot_group)
    print("min_reads:", min_reads)
    print("max_reads:", max_reads)
    print("ar_specific:", ar_specific)
    print("ar_start:", ar_start)
    print("ar_end:", ar_end)
    print("member:", member)
    data_info, download_status, file_zip = sra_download_main(accession, alignment_filter_type, alignment_filter,
                                                             compression, skip_technical, remove_adapter,
                                                             spot_group, min_reads, max_reads,
                                                             ar_specific, ar_start, ar_end, member)
    return data_info, download_status, file_zip

# ------------------ GRADIO GUI ------------------
with gr.Blocks(title="NGS Sequence Quality Check") as demo:
    gr.Markdown("# NGS Sequence Quality Check")
    gr.Markdown("Streamline NGS workflows for quality checking using the SRA Toolkit, FastQC, and Fastp.")
    
    with gr.Tab("Setup Environment"):
        gr.Markdown("## Setup Environment & Install Dependencies")
        sudo_input = gr.Textbox(label="Enter Sudo Password", type="password", placeholder="Sudo Password")
        setup_button = gr.Button("Run Setup")
        setup_output = gr.Textbox(label="Setup Log", interactive=False)
        setup_button.click(fn=run_setup, inputs=sudo_input, outputs=setup_output)
    
    with gr.Tab("SRA Downloader") as webui:
        gr.Markdown("## SRA Toolkit")
        with gr.Row():
            with gr.Column():
                accession = gr.Textbox(label="Enter SRA Number", placeholder="ERR11468775", interactive=True)
                with gr.Column():
                    compression = gr.Checkbox(label="Compress", value=True)
                    skip_technical = gr.Checkbox(label="Skip Technical details", value=False)
                    remove_adapter = gr.Checkbox(label="Remove Adapter", value=False)
                    spot_group = gr.Checkbox(label="Enable Spot Grouping", value=False)
                    member = gr.Textbox(label="Member", placeholder="Enter Member", interactive=True, visible=False)
            with gr.Column():
                apply_min_max_reads = gr.Checkbox(label="Enable Min & Max Reads Count", value=False)
                min_reads = gr.Number(label="Minimum Reads", visible=False)
                max_reads = gr.Number(label="Maximum Reads", visible=False)
            with gr.Column():
                alignment_filter = gr.Checkbox(label="Apply Alignment Filters", value=False)
                alignment_filter_type = gr.Radio(label="Alignment Filter Type",
                                                 choices=["split-spot", "aligned", "unaligned", "aligned-region", "matepair-distance"],
                                                 visible=False)
            with gr.Column():
                ar_specific = gr.Textbox(label="Aligned Region Specific", placeholder="Enter Specific Region", interactive=True, visible=False)
                ar_start = gr.Number(label="Aligned Region Start", visible=False)
                ar_end = gr.Number(label="Aligned Region End", visible=False)
            apply_min_max_reads.change(fn=enable_reads_count, inputs=apply_min_max_reads, outputs=[min_reads, max_reads])
            alignment_filter.change(fn=enable_alignment_filter, inputs=alignment_filter, outputs=[alignment_filter_type])
            alignment_filter_type.change(fn=enable_alignment_filter_type, inputs=alignment_filter_type, outputs=[ar_specific, ar_start, ar_end])
            spot_group.change(fn=enable_spot_group, inputs=spot_group, outputs=[member])
            btn2 = gr.Button(value="Download SRA Data")
        with gr.Row():
            data = gr.Textbox(label="Data", placeholder="Data", lines=10, interactive=True)
            download_status = gr.Textbox(label="Download Status", placeholder="Download Status", lines=5, interactive=True)
            files = gr.File(label="Download your File")
        btn2.click(fn=get_fastq,
                   inputs=[accession, alignment_filter_type, alignment_filter, compression, skip_technical,
                           remove_adapter, spot_group, min_reads, max_reads, ar_specific, ar_start, ar_end, member],
                   outputs=[data, download_status, files])
    
    with gr.Tab("FastQC"):
        gr.Markdown("## FastQC Tool")
        gr.Markdown("Upload unzipped FASTQ/FASTA files (forward and reverse reads).")
        fastqc_files_input = gr.File(label="Upload FASTQ/FASTA Files", file_count="multiple")
        fastqc_run_button = gr.Button("Run FastQC")
        fastqc_log = gr.Textbox(label="FastQC Log", interactive=False)
        fastqc_reports = gr.File(label="FastQC Reports", file_count="multiple")
        fastqc_run_button.click(fn=fastqc_main,
                                inputs=fastqc_files_input,
                                outputs=[fastqc_log, fastqc_reports])
    
    with gr.Tab("Fastp"):
        gr.Markdown("## Fastp Tool")
        gr.Markdown("Upload FASTQ files for adapter trimming (Forward and Reverse).")
        fastp_files_input = gr.File(label="Upload FASTQ Files", file_count="multiple")
        fastp_run_button = gr.Button("Run Fastp")
        fastp_log = gr.Textbox(label="Fastp Log", interactive=False)
        fastp_reports = gr.File(label="Trimmed FASTQ Files", file_count="multiple")
        fastp_run_button.click(fn=fastp_main,
                               inputs=fastp_files_input,
                               outputs=[fastp_log, fastp_reports])
    
    try:
        webui.queue(default_concurrency_limit=25)
    except Exception as e:
        print(f"Queue error: {e}")
    
demo.launch()