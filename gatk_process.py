# docker, GATK, bcftools and samtools

import os
from dotenv import load_dotenv
from tools import run_command_out, set_paths

load_dotenv()
working_dir = os.getenv("WORKING_DIR")
docker_path = os.getenv("DOCKER_PATH")
gatk_path = os.getenv("GATK_PATH")
bcftools_path = os.getenv("BCFTOOLS_PATH")
samtools_path = os.getenv("SAMTOOLS_PATH")



