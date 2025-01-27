import os
import tarfile
from dotenv import load_dotenv
from tools import run_command_out

load_dotenv()
app_dir = os.getenv("APP_DIR")
data_dir = os.getenv("DATA_DIR")

def download_ref_genome():
    ref_genome_path = os.path.join(data_dir, "ref_genome")
    os.makedirs(ref_genome_path, exist_ok=True)
    
    #try:
    ref_genome_file = os.path.join(ref_genome_path, "chr18.fa")
    if os.path.exists(ref_genome_file):
        print(f"Reference genome already exists.")
        return

    # except Exception as e:
    #     print(f"An error occurred while checking for reference genome: {e}")
        
    print(f"Downloading reference genome...")
    download_url = "https://hgdownload.soe.ucsc.edu/goldenPath/hg38/chromosomes/chr18.fa.gz"
    run_command_out(f"wget -O {ref_genome_path}/ref_genome.gz {download_url}")
    run_command_out(f"gunzip {ref_genome_path}/ref_genome.gz")
    run_command_out(f"mv {ref_genome_path}/ref_genome {ref_genome_path}/chr18.fa")
    print(f"Reference genome downloaded and unzipped successfully.")

if __name__ == '__main__':
    download_ref_genome()