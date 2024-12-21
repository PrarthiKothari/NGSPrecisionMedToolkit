import os, sys
import tarfile
from dotenv import load_dotenv
from tools import run_command_out, set_paths

load_dotenv()
app_dir = os.getenv("APP_DIR")
data_dir = os.getenv("DATA_DIR")

def download_ref_genome():
    ref_genome_path = f"{data_dir}/ref_genome"
    os.makedirs(ref_genome_path, exist_ok=True)
    try:
        run_command_out("ref_genome", dir=ref_genome_path)
    except:
        run_command_out(f"wget -O {ref_genome_path}/ref_genome.gz https://hgdownload.soe.ucsc.edu/goldenPath/hg38/chromosomes/chr18.fa.gz")
        run_command_out(f"gunzip {ref_genome_path}/ref_genome.gz -C {ref_genome_path}")