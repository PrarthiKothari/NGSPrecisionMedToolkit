import os, sys
import tarfile
from dotenv import load_dotenv
from tools import run_command_out, set_paths

load_dotenv()
fastqc_path = os.getenv("FASTQC_PATH")
working_dir = os.getenv("WORKING_DIR")

def fastqc_check(file, working_dir):
    file_path = os.path.join(working_dir, file)
    if os.path.isfile(file_path):
        if any(ext in file for ext in [".fastq", ".sam", ".bam"]):
            try:
                output_dir = os.path.join(working_dir, 'fastqc_reports')
                os.makedirs(output_dir, exist_ok=True)
                run_command_out(f"fastqc {file_path} --outdir {output_dir}", dir=fastqc_path)
            except Exception as e:
                print(f"An error occurred while running the command: {e}")
        else:
            print(f"The file format of {file} is not supported.")
    
def main(working_dir):
    fastqc_data_dir = os.path.join(working_dir, 'fastqc_reports')
    set_paths("FASTQC_DATA_DIR", fastqc_data_dir)
    files = os.listdir(working_dir)
    for file in files:
        fastqc_check(file, working_dir)
    files = os.listdir(fastqc_data_dir)
    reports = []
    for file in files:
        if 'html' in file:
            report = os.path.join(fastqc_data_dir, file)
            print(f"FastQC report for {file.strip('.html').replace('_fastqc', '.fastq.gz')} is ready at {report}")
            reports.append(file)
    return reports

if __name__ == '__main__':
    main(working_dir)
