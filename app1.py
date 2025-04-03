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

# ------------------ REFERENCE GENOME INTEGRATION ------------------
def download_reference_genome(url=None, custom_name=None):
    working_dir = os.getenv("WORKING_DIR")
    if not working_dir:
        return "Working directory not set. Run the SRA download step first."
    
    ref_dir = os.path.join(working_dir, "reference")
    os.makedirs(ref_dir, exist_ok=True)
    
    if not url:
        return "No URL provided for reference genome download."
    
    try:
        # Extract filename from URL
        filename = os.path.basename(url)
        if custom_name:
            # Use custom name but preserve extension
            ext = os.path.splitext(filename)[1]
            filename = f"{custom_name}{ext}"
        
        compressed_path = os.path.join(ref_dir, filename)
        
        # Download the file
        print(f"Downloading reference genome from {url}...")
        run_command_out(f"wget -O {compressed_path} {url}")
        
        # Handle different compression formats
        if filename.endswith('.gz'):
            print("Decompressing gzip file...")
            run_command_out(f"gunzip {compressed_path}")
            uncompressed_path = compressed_path[:-3]  # remove .gz
        elif filename.endswith('.zip'):
            print("Extracting zip file...")
            run_command_out(f"unzip {compressed_path} -d {ref_dir}")
            os.remove(compressed_path)
            # Assume the first .fa/.fasta file is the reference
            uncompressed_path = None
            for f in os.listdir(ref_dir):
                if f.endswith(('.fa', '.fasta', '.fna')):
                    uncompressed_path = os.path.join(ref_dir, f)
                    break
            if not uncompressed_path:
                return "No FASTA file found in the downloaded archive."
        elif filename.endswith('.tar.gz') or filename.endswith('.tgz'):
            print("Extracting tar.gz file...")
            with tarfile.open(compressed_path, "r:gz") as tar:
                tar.extractall(path=ref_dir)
            os.remove(compressed_path)
            # Assume the first .fa/.fasta file is the reference
            uncompressed_path = None
            for f in os.listdir(ref_dir):
                if f.endswith(('.fa', '.fasta', '.fna')):
                    uncompressed_path = os.path.join(ref_dir, f)
                    break
            if not uncompressed_path:
                return "No FASTA file found in the downloaded archive."
        else:
            uncompressed_path = compressed_path
        
        # If we have a custom name and the file was compressed, rename it
        if custom_name and uncompressed_path.endswith(('.fa', '.fasta', '.fna')):
            final_path = os.path.join(ref_dir, f"{custom_name}{os.path.splitext(uncompressed_path)[1]}")
            os.rename(uncompressed_path, final_path)
            uncompressed_path = final_path
        
        # Index the reference genome
        print("Indexing reference genome...")
        run_command_out(f"bwa index {uncompressed_path}")
        run_command_out(f"samtools faidx {uncompressed_path}")
        dict_path = uncompressed_path.replace('.fa', '.dict').replace('.fasta', '.dict').replace('.fna', '.dict')
        run_command_out(f"gatk CreateSequenceDictionary -R {uncompressed_path} -O {dict_path}")
        
        return f"Reference genome downloaded and indexed successfully at {uncompressed_path}"
    
    except Exception as e:
        return f"Error downloading reference genome: {str(e)}"

def load_reference_genome(ref_genome_file=None, genome_url=None, custom_name=None):
    working_dir = os.getenv("WORKING_DIR")
    if not working_dir:
        return "Working directory not set. Run the SRA download step first."
    
    # Create reference genome directory
    ref_dir = os.path.join(working_dir, "reference")
    os.makedirs(ref_dir, exist_ok=True)
    
    if genome_url:
        # Download from URL
        return download_reference_genome(genome_url, custom_name)
    elif ref_genome_file:
        # Handle uploaded file
        dest_path = os.path.join(ref_dir, os.path.basename(ref_genome_file.name))
        if custom_name:
            # Preserve extension
            ext = os.path.splitext(ref_genome_file.name)[1]
            dest_path = os.path.join(ref_dir, f"{custom_name}{ext}")
        
        shutil.copy(ref_genome_file.name, dest_path)
        
        # Index the reference genome if FASTA
        if dest_path.endswith(('.fa', '.fasta', '.fna')):
            try:
                # BWA index
                run_command_out(f"bwa index {dest_path}")
                # SAMtools index
                run_command_out(f"samtools faidx {dest_path}")
                # Create dictionary
                dict_path = dest_path.replace('.fa', '.dict').replace('.fasta', '.dict').replace('.fna', '.dict')
                run_command_out(f"gatk CreateSequenceDictionary -R {dest_path} -O {dict_path}")
                return f"Reference genome loaded and indexed successfully at {dest_path}"
            except Exception as e:
                return f"Error indexing reference genome: {e}"
        return f"Reference genome loaded successfully at {dest_path}"
    else:
        return "No reference genome file or URL provided."
    
# ------------------ BWA ALIGNMENT INTEGRATION ------------------
def run_bwa_alignment(reads_files, ref_genome_name=None, threads=4, algorithm="mem"):
    working_dir = os.getenv("WORKING_DIR")
    if not working_dir:
        return "Working directory not set. Run the SRA download step first.", None
    
    # Find reference genome
    ref_dir = os.path.join(working_dir, "reference")
    if not os.path.exists(ref_dir):
        return "Reference genome directory not found. Load a reference genome first.", None
    
    # If no specific reference genome provided, use the first one found
    if not ref_genome_name:
        ref_files = [f for f in os.listdir(ref_dir) if f.endswith(('.fa', '.fasta', '.fna'))]
        if not ref_files:
            return "No reference genome found in reference directory.", None
        ref_genome_name = ref_files[0]
    
    ref_path = os.path.join(ref_dir, ref_genome_name)
    
    # Create BWA index directory and files
    bwa_data_dir = os.path.join(working_dir, 'bwa_index_map')
    os.makedirs(bwa_data_dir, exist_ok=True)
    ref_prefix = os.path.join(bwa_data_dir, os.path.splitext(ref_genome_name)[0] + '_ref')
    
    # Create alignment output directory
    align_dir = os.path.join(working_dir, "alignment")
    os.makedirs(align_dir, exist_ok=True)
    
    try:
        # Index the reference genome if not already indexed
        if not os.path.exists(f"{ref_prefix}.bwt"):
            print("Indexing reference genome...")
            run_command_out(f"bwa index -a bwtsw -p {ref_prefix} {ref_path}")
        
        # Process reads files
        if len(reads_files) == 1:
            # Single-end reads
            reads_file = os.path.join(working_dir, os.path.basename(reads_files[0].name))
            shutil.copy(reads_files[0].name, reads_file)
            
            output_sam = os.path.join(align_dir, "aligned.sam")
            cmd = f"bwa {algorithm} {ref_prefix} {reads_file} -t {threads} -o {output_sam}"
        elif len(reads_files) == 2:
            # Paired-end reads
            reads1 = os.path.join(working_dir, os.path.basename(reads_files[0].name))
            reads2 = os.path.join(working_dir, os.path.basename(reads_files[1].name))
            shutil.copy(reads_files[0].name, reads1)
            shutil.copy(reads_files[1].name, reads2)
            
            output_sam = os.path.join(align_dir, "aligned.sam")
            cmd = f"bwa {algorithm} {ref_prefix} {reads1} {reads2} -t {threads} -o {output_sam}"
        else:
            return "Please provide either 1 (single-end) or 2 (paired-end) reads files.", None
        
        print(f"Running BWA command: {cmd}")
        run_command_out(cmd)
        
        # Convert SAM to BAM and index
        output_bam = output_sam.replace('.sam', '.bam')
        run_command_out(f"samtools view -S -b {output_sam} > {output_bam}")
        sorted_bam = output_bam.replace('.bam', '.sorted.bam')
        run_command_out(f"samtools sort {output_bam} -o {sorted_bam}")
        run_command_out(f"samtools index {sorted_bam}")
        
        # Clean up intermediate files
        os.remove(output_sam)
        os.remove(output_bam)
        
        return "BWA alignment completed successfully.", sorted_bam
    except Exception as e:
        return f"Error during BWA alignment: {e}", None

# ------------------ GATK ANALYSIS INTEGRATION ------------------
def download_gatk_resources(analysis_dir):
    """Download required GATK resource files"""
    resources = {
        "dbsnp": {
            "vcf": "https://storage.googleapis.com/genomics-public-data/resources/broad/hg38/v0/Homo_sapiens_assembly38.dbsnp138.vcf",
            "idx": "https://storage.googleapis.com/genomics-public-data/resources/broad/hg38/v0/Homo_sapiens_assembly38.dbsnp138.vcf.idx"
        },
        "hapmap": {
            "vcf": "https://storage.googleapis.com/genomics-public-data/resources/broad/hg38/v0/hapmap_3.3.hg38.vcf.gz",
            "tbi": "https://storage.googleapis.com/genomics-public-data/resources/broad/hg38/v0/hapmap_3.3.hg38.vcf.gz.tbi"
        }
    }
    
    log = ""
    for res_name, urls in resources.items():
        vcf_path = os.path.join(analysis_dir, os.path.basename(urls["vcf"]))
        idx_path = os.path.join(analysis_dir, os.path.basename(urls["idx"]))
        
        if not os.path.exists(vcf_path):
            log += f"Downloading {res_name} VCF...\n"
            run_command_out(f"wget {urls['vcf']} -O {vcf_path}")
        else:
            log += f"{res_name} VCF already exists.\n"
            
        if not os.path.exists(idx_path):
            log += f"Downloading {res_name} index...\n"
            run_command_out(f"wget {urls['idx']} -O {idx_path}")
        else:
            log += f"{res_name} index already exists.\n"
    
    return log

def run_gatk_analysis(bam_file, run_mode="full", skip_downloads=False):
    working_dir = os.getenv("WORKING_DIR")
    if not working_dir:
        return "Working directory not set. Run the SRA download step first.", None
    
    # Create analysis directory
    analysis_dir = os.path.join(working_dir, "gatk_analysis")
    os.makedirs(analysis_dir, exist_ok=True)
    
    # Find reference genome
    ref_dir = os.path.join(working_dir, "reference")
    if not os.path.exists(ref_dir):
        return "Reference genome directory not found. Load a reference genome first.", None
    
    ref_files = [f for f in os.listdir(ref_dir) if f.endswith(('.fa', '.fasta', '.fna'))]
    if not ref_files:
        return "No reference genome found in reference directory.", None
    
    ref_path = os.path.join(ref_dir, ref_files[0])
    
    try:
        log = "Starting GATK analysis...\n"
        
        # Copy BAM file to analysis directory
        bam_path = os.path.join(analysis_dir, os.path.basename(bam_file.name))
        shutil.copy(bam_file.name, bam_path)
        log += f"Copied BAM file to {bam_path}\n"
        
        # Download resource files if needed
        if not skip_downloads:
            log += download_gatk_resources(analysis_dir)
        
        # Define output files
        output_files = []
        
        # 1. Add read groups
        with_rg_bam = os.path.join(analysis_dir, "sample_withRG.bam")
        run_command_out(f"gatk AddOrReplaceReadGroups -I {bam_path} -O {with_rg_bam} "
                       f"-ID 1 -LB lib1 -PL ILLUMINA -PU unit1 -SM sample1")
        log += "Added read groups to BAM file\n"
        
        # 2. Sort BAM file
        sorted_bam = os.path.join(analysis_dir, "sample_sorted.bam")
        run_command_out(f"gatk SortSam -I {with_rg_bam} -O {sorted_bam} -SO coordinate")
        log += "Sorted BAM file\n"
        
        # 3. Mark duplicates
        marked_bam = os.path.join(analysis_dir, "sample_marked.bam")
        metrics_file = os.path.join(analysis_dir, "marked_dup_metrics.txt")
        run_command_out(f"gatk MarkDuplicates -I {sorted_bam} -O {marked_bam} -M {metrics_file}")
        log += "Marked duplicates\n"
        
        # 4. Create BQSR table
        dbsnp_vcf = os.path.join(analysis_dir, "Homo_sapiens_assembly38.dbsnp138.vcf")
        recal_table = os.path.join(analysis_dir, "sample_recal_data.table")
        run_command_out(f"gatk BaseRecalibrator -I {marked_bam} -R {ref_path} "
                       f"--known-sites {dbsnp_vcf} -O {recal_table}")
        log += "Created BQSR table\n"
        
        # 5. Apply BQSR
        recal_bam = os.path.join(analysis_dir, "sample_recal.bam")
        run_command_out(f"gatk ApplyBQSR -R {ref_path} -I {marked_bam} "
                       f"--bqsr-recal-file {recal_table} -O {recal_bam}")
        log += "Applied base quality score recalibration\n"
        
        # 6. Variant calling based on run mode
        if run_mode in ["full", "germline"]:
            # Germline variant calling
            vcf_output = os.path.join(analysis_dir, "sample_variants.vcf.gz")
            run_command_out(f"gatk HaplotypeCaller -R {ref_path} -I {recal_bam} "
                           f"-O {vcf_output} -ERC GVCF")
            output_files.append(vcf_output)
            log += "Performed germline variant calling\n"
            
            if run_mode == "full":
                # Additional filtering
                filtered_vcf = os.path.join(analysis_dir, "sample_filtered.vcf.gz")
                run_command_out(f"gatk VariantFiltration -R {ref_path} -V {vcf_output} "
                               f"-O {filtered_vcf} --filter-expression 'QD < 2.0 || FS > 60.0 || MQ < 40.0' "
                               f"--filter-name 'basic_filter'")
                output_files.append(filtered_vcf)
                log += "Applied variant filtering\n"
        
        if run_mode in ["full", "somatic"]:
            # Somatic variant calling
            somatic_vcf = os.path.join(analysis_dir, "sample_somatic.vcf.gz")
            run_command_out(f"gatk Mutect2 -R {ref_path} -I {recal_bam} "
                           f"-O {somatic_vcf} --germline-resource {dbsnp_vcf}")
            output_files.append(somatic_vcf)
            log += "Performed somatic variant calling\n"
            
            if run_mode == "full":
                # Filter somatic variants
                filtered_somatic = os.path.join(analysis_dir, "sample_somatic_filtered.vcf.gz")
                run_command_out(f"gatk FilterMutectCalls -R {ref_path} -V {somatic_vcf} "
                               f"-O {filtered_somatic}")
                output_files.append(filtered_somatic)
                log += "Filtered somatic variants\n"
        
        # Create index for all VCF files
        for vcf in output_files:
            if vcf.endswith(".vcf.gz"):
                run_command_out(f"gatk IndexFeatureFile -I {vcf}")
        
        # Return the primary output file
        if output_files:
            primary_output = output_files[0]
            if run_mode == "full":
                primary_output = filtered_vcf if "filtered_vcf" in locals() else output_files[-1]
            return log, primary_output
        else:
            return log + "Analysis completed but no variant files were generated.", None
    
    except Exception as e:
        return f"Error during GATK analysis: {str(e)}", None
    
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
with gr.Blocks(title="NGS-Precision Medicine Toolkit") as demo:
    gr.Markdown("# NGS-Precision Medicine Toolkit")
    gr.Markdown("Streamlining NGS workflows for Applications of Precision Medicine")
    
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

    with gr.Tab("Reference Genome"):
        gr.Markdown("## Reference Genome Selection")
        with gr.Row():
            with gr.Column():
                gr.Markdown("### Option 1: Upload Local File")
                ref_genome_file = gr.File(label="Upload Reference Genome (FASTA/FASTQ)")
                custom_name_upload = gr.Textbox(label="Custom Name (optional)", placeholder="e.g., hg38_chr18")
            with gr.Column():
                gr.Markdown("### Option 2: Download from URL")
                genome_url = gr.Textbox(label="Reference Genome URL", 
                                      placeholder="e.g., https://hgdownload.soe.ucsc.edu/goldenPath/hg38/chromosomes/chr18.fa.gz")
                custom_name_url = gr.Textbox(label="Custom Name (optional)", placeholder="e.g., hg38_chr18")
                example_urls = gr.Dropdown(
                    label="Example URLs",
                    choices=[
                        "UCSC hg38 chr18",
                        "UCSC hg38 chrM",
                        "GRCh38 primary assembly"
                    ],
                    value="Select an example"
                )
                
                def update_url(example):
                    urls = {
                        "UCSC hg38 chr18": "https://hgdownload.soe.ucsc.edu/goldenPath/hg38/chromosomes/chr18.fa.gz",
                        "UCSC hg38 chrM": "https://hgdownload.soe.ucsc.edu/goldenPath/hg38/chromosomes/chrM.fa.gz",
                        "GRCh38 primary assembly": "https://ftp.ncbi.nlm.nih.gov/genomes/all/GCA/000/001/405/GCA_000001405.15_GRCh38/seqs_for_alignment_pipelines.ucsc_ids/GCA_000001405.15_GRCh38_no_alt_analysis_set.fna.gz"
                    }
                    return gr.update(value=urls.get(example, ""))
                
                example_urls.change(fn=update_url, inputs=example_urls, outputs=genome_url)
        
        ref_genome_button = gr.Button("Load Reference Genome")
        ref_genome_log = gr.Textbox(label="Reference Genome Log", interactive=False)
        
        ref_genome_button.click(
            fn=load_reference_genome,
            inputs=[ref_genome_file, genome_url],
            outputs=ref_genome_log
        )
    
    with gr.Tab("BWA Alignment"):
        gr.Markdown("## BWA Alignment")
        with gr.Row():
            with gr.Column():
                reads_file = gr.File(label="Upload Reads File (FASTQ)", file_count="multiple")
                ref_genome_dropdown = gr.Dropdown(
                    label="Select Reference Genome",
                    choices=[],
                    interactive=True
                )
                
                def update_ref_genome_dropdown():
                    working_dir = os.getenv("WORKING_DIR")
                    if not working_dir:
                        return gr.update(choices=[])
                    
                    ref_dir = os.path.join(working_dir, "reference")
                    if not os.path.exists(ref_dir):
                        return gr.update(choices=[])
                    
                    ref_files = [f for f in os.listdir(ref_dir) if f.endswith(('.fa', '.fasta', '.fna'))]
                    return gr.update(choices=ref_files)
                
            with gr.Column():
                algorithm = gr.Radio(
                    label="Alignment Algorithm",
                    choices=["mem", "aln", "bwasw"],
                    value="mem",
                    interactive=True
                )
                threads = gr.Slider(
                    label="Number of Threads",
                    minimum=1,
                    maximum=32,
                    value=4,
                    step=1,
                    interactive=True
                )
        
        bwa_run_button = gr.Button("Run BWA Alignment")
        bwa_log = gr.Textbox(label="BWA Log", interactive=False)
        aligned_output = gr.File(label="Aligned Output (BAM)")
        
        # Update reference genome dropdown when tab is selected
        demo.load(
            fn=update_ref_genome_dropdown,
            inputs=[],
            outputs=[ref_genome_dropdown],
            queue=False
        )
        
        bwa_run_button.click(
            fn=run_bwa_alignment,
            inputs=[reads_file, ref_genome_dropdown, threads, algorithm],
            outputs=[bwa_log, aligned_output]
        )
    
    with gr.Tab("GATK Analysis"):
        gr.Markdown("## GATK Variant Analysis")
        with gr.Row():
            with gr.Column():
                bam_file = gr.File(label="Upload Aligned Reads (BAM)", file_count="single")
                ref_genome_dropdown = gr.Dropdown(
                    label="Select Reference Genome",
                    choices=[],
                    interactive=True
                )
                
                def update_ref_genome_dropdown():
                    working_dir = os.getenv("WORKING_DIR")
                    if not working_dir:
                        return gr.update(choices=[])
                    
                    ref_dir = os.path.join(working_dir, "reference")
                    if not os.path.exists(ref_dir):
                        return gr.update(choices=[])
                    
                    ref_files = [f for f in os.listdir(ref_dir) if f.endswith(('.fa', '.fasta', '.fna'))]
                    return gr.update(choices=ref_files)
                
            with gr.Column():
                analysis_mode = gr.Radio(
                    label="Analysis Mode",
                    choices=["Full", "Germline", "Somatic"],
                    value="Full",
                    interactive=True
                )
                skip_downloads = gr.Checkbox(
                    label="Skip downloading resource files (use existing)",
                    value=False,
                    interactive=True
                )
        
        gatk_run_button = gr.Button("Run GATK Analysis")
        gatk_log = gr.Textbox(label="GATK Log", interactive=False, lines=10)
        vcf_output = gr.File(label="Variant Call File (VCF)")
        
        # Update reference genome dropdown when tab is selected
        demo.load(
            fn=update_ref_genome_dropdown,
            inputs=[],
            outputs=[ref_genome_dropdown],
            queue=False
        )
        
        gatk_run_button.click(
            fn=run_gatk_analysis,
            inputs=[bam_file, analysis_mode, skip_downloads],
            outputs=[gatk_log, vcf_output]
        )
    
    try:
        webui.queue(default_concurrency_limit=25)
    except Exception as e:
        print(f"Queue error: {e}")
    
demo.launch()