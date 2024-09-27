import os
from dotenv import load_dotenv

load_dotenv()
working_dir = os.getenv("WORKING_DIR")
fastp_path = os.getenv("FASTP_PATH")