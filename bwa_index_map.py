import os
from dotenv import load_dotenv
from tools import run_command_out, set_paths

load_dotenv()
working_dir = os.getenv("WORKING_DIR")
bwa_path = "bwa"
data_dir = os.getenv("DATA_DIR")

def bwa_index_map(trimmed_fastq_file_1, trimmed_fastq_file_2, ref_genome):
    bwa_data_dir = os.path.join(working_dir, 'bwa_index_map')
    os.makedirs(bwa_data_dir, exist_ok=True)
    chr18_ref = os.path.join(bwa_data_dir, 'chr18_ref')

    print("Indexing reference genome...")
    run_command_out(f"{bwa_path} index -a bwtsw -p {chr18_ref} {ref_genome}")

    print("Mapping trimmed FASTQ files...")
    sam_output_file = os.path.join(bwa_data_dir, "sample1.sam")
    run_command_out(f"{bwa_path} mem {chr18_ref} {trimmed_fastq_file_1} {trimmed_fastq_file_2} -t 10 -o {sam_output_file}")
    
    print(f"Mapping completed. Output SAM file: {sam_output_file}")
    return sam_output_file

def main(working_dir):
    bwa_data_dir = os.path.join(working_dir, 'bwa_index_map')
    set_paths("BWA_DATA_DIR", bwa_data_dir)

    trimmed_fastq_file_1 = os.path.join(working_dir, "trimmed", "ERR11468775_1_trimmed.fastq.gz")
    trimmed_fastq_file_2 = os.path.join(working_dir, "trimmed", "ERR11468775_2_trimmed.fastq.gz")
    ref_genome = os.path.join(data_dir, "ref_genome", "chr18.fa")

    samfile_1 = bwa_index_map(trimmed_fastq_file_1, trimmed_fastq_file_2, ref_genome)

    return samfile_1

if __name__ == '__main__':
    mapped_files = main(working_dir)
    
    print(f"Mapped files: {mapped_files}")
