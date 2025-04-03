import os
from dotenv import load_dotenv
from tools import run_command_out, set_paths

load_dotenv()
working_dir = os.getenv("WORKING_DIR")
fastp_path = os.getenv("FASTP_PATH")

def trim_adapters(fastq_file_1, fastq_file_2):
    output_dir = os.path.join(working_dir, 'fastp_reports')
    os.makedirs(output_dir, exist_ok=True)

    output_file_1 = os.path.join(working_dir, f"{os.path.basename(fastq_file_1).replace('.fastq.gz', '_trimmed.fastq.gz')}")
    output_file_2 = os.path.join(working_dir, f"{os.path.basename(fastq_file_2).replace('.fastq.gz', '_trimmed.fastq.gz')}")

    # Construct the command for fastp
    command = (
        f"{fastp_path}/fastp"
        f" -i {fastq_file_1}"
        f" -o {output_file_1}"
        f" -I {fastq_file_2}"
        f" -O {output_file_2}"
        f" --detect_adapter_for_pe"
        f" -f 10 -g -l 50"
        f" -c -h {output_dir}/ERR11468775_fastp.html"
        f" -w 10"
    )

    try:
        run_command_out(command)
        print(f"Trimmed files created: {output_file_1}, {output_file_2}")
    except Exception as e:
        print(f"Error trimming adapters: {e}")
    
    return output_file_1, output_file_2

def main(working_dir):
    fastp_data_dir = os.path.join(working_dir, 'fastp_reports')
    set_paths("FASTP_DATA_DIR", fastp_data_dir)

    fastq_file_1 = os.path.join(working_dir, "ERR11468775_1.fastq.gz")
    fastq_file_2 = os.path.join(working_dir, "ERR11468775_2.fastq.gz")

    trimmed_files = []
    output_file_1, output_file_2 = trim_adapters(fastq_file_1, fastq_file_2)
    trimmed_files.append(output_file_1)
    trimmed_files.append(output_file_2)

    return trimmed_files

if __name__ == '__main__':
    trimmed_files = main(working_dir)
    data_dir = os.path.join(working_dir, 'trimmed')
    os.makedirs(data_dir, exist_ok=True)
    for file in trimmed_files:
        trimmed_path = os.path.join(data_dir, os.path.basename(file))
        os.rename(file, trimmed_path)
        print(f"Moved {file} to {trimmed_path}")