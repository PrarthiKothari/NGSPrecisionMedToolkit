import os
from dotenv import load_dotenv
from tools import run_command_out, set_paths

load_dotenv()
working_dir = os.getenv("WORKING_DIR")
fastp_path = os.getenv("FASTP_PATH")

def trim_adapters(fastq_file_1, fastq_file_2):
    output_dir = os.path.join(working_dir, 'fastp_reports')
    os.makedirs(output_dir, exist_ok=True)

    output_file_1 = f"{working_dir}/{os.path.basename(fastq_file_1).replace('.fastq.gz', '_trimmed.fastq.gz')}"
    output_file_2 = f"{working_dir}/{os.path.basename(fastq_file_2).replace('.fastq.gz', '_trimmed.fastq.gz')}"

    run_command_out(f"{fastp_path}/fastp -i {fastq_file_1} -o {output_file_1} -I {fastq_file_2} -O {output_file_2} 
                    --detect_adapter_for_pe -f 10 -g -l 50 -c -h {output_dir}/ERR11468776_fastp.html -w 10")
    return output_file_1, output_file_2

def main(working_dir):
    fastp_data_dir = os.path.join(working_dir, 'fastp_reports')
    set_paths("FASTP_DATA_DIR", fastp_data_dir)

    files = os.listdir(working_dir)
    trimmed_files = []
    output_file_1, output_file_2 = trim_adapters(f"{working_dir}/ERR11468776_1.fastq.gz", f"{working_dir}/ERR11468776_2.fastq.gz")
    trimmed_files.append(output_file_1)
    trimmed_files.append(output_file_2)

    return trimmed_files

if __name__ == '__main__':
    trimmed_files = main(working_dir)
    data_dir = os.path.join(working_dir, 'trimmed')
    os.makedirs(data_dir, exist_ok=True)
    '''
    trimmed_files = []

    for file in trimmed_files:
        trimmed = os.path.join(data_dir, os.path.basename(file))
        trimmed_files.append(file)
    '''