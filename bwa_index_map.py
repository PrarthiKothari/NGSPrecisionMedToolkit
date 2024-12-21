import os
from dotenv import load_dotenv
from tools import run_command_out, set_paths

load_dotenv()
working_dir = os.getenv("WORKING_DIR")
bwa_path = os.getenv("BWA_PATH")

def bwa_index_map(trimmed_fastq_file_1, trimmed_fastq_file_2):
    bwa_sam_dir = os.path.join(working_dir, 'bwa_index_map')
    os.makedirs(bwa_sam_dir, exist_ok=True)

    run_command_out(f"{bwa_path}/bwa index -a bwtsw -p chr18_ref chr18.fasta") # remaining ref_genome rename
    run_command_out(f"{bwa_path}/bwa mem chr18_ref {trimmed_fastq_file_1} {trimmed_fastq_file_2} -t 10 -o {bwa_sam_dir}/sample1.sam")
    
    return f"{bwa_sam_dir}/sample1.sam"

def main(working_dir):
    bwa_data_dir = os.path.join(working_dir, 'bwa_index_map')
    set_paths("BWA_DATA_DIR", bwa_data_dir)

    files = os.listdir(working_dir)
    #mapped_files = []
    samfile_1 = bwa_index_map(f"{working_dir}/ERR11468776_1_trimmed.fastq.gz", f"{working_dir}/ERR11468776_2_trimmed.fastq.gz")
    #mapped_files.append(samfile_1)

    return samfile_1
    #return mapped_files

if __name__ == '__main__':
    mapped_files = main(working_dir)
    
    #for file in mapped_files:
    #    print(file)