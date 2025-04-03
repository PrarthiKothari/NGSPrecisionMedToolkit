import os
import sys
from dotenv import load_dotenv
from tools import run_command_out, set_paths

load_dotenv()
app_dir = os.getenv("APP_DIR")
data_dir = os.getenv("DATA_DIR")
sratoolkit_path = os.getenv("SRATOOLKIT_PATH")

def cmd_for_info(accession: str):
    command = (f'vdb-dump {accession} --info')
    return command

def cmd_to_download(accession: str,
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
    command = ['fastq-dump', accession, '--split-3', '--outdir', f'data/{accession}']
    if compressed:
        command.append('--gzip')
    else:
        command = command
    if alignment_filter:
        if alignment_filter_type == "split-spot":
            command.remove('--split-3')
            command.append('--split-spot')
        elif alignment_filter_type == "aligned":
            command.remove('--split-3')
            command.append('--aligned')
        elif alignment_filter_type == "unaligned":
            command.remove('--split-3')
            command.append('--unaligned')
        elif alignment_filter_type == "aligned-region":
            command.remove('--split-3')
            command.append('--aligned-region')
            command.append(f'{ar_specific}:{ar_start}-{ar_end}')
        elif alignment_filter_type == "matepair-distance":
            command.remove('--split-3')
            command.append('--matepair-distance')
            command.append(f'{ar_start}-{ar_end}')
        else:
            command = command
    else:
        command = command
    if skip_technical:
        command.append('--skip-technical')
    else:
        command = command
    if min_reads:
        command.append(f'--minSpotId')
        command.append(str(min_reads))
    else:
        command = command
    if max_reads:
        command.append(f'--maxSpotId')
        command.append(str(max_reads))
    else:
        command = command
    if remove_adapter:
        command.append('--clip')
    else:
        command = command
    if spot_group:
        command.append('--spot-group')
        command.append(member)
    else:
        command = command
    cmd = ' '.join(command)
    return cmd

def list_files_in_directory(directory):
    try:
        # List all files in the specified directory
        files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
        return files
    except FileNotFoundError:
        print(f"The directory '{directory}' does not exist.")
        return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []

def main(accession: str, alignment_filter_type: str,
         alignment_filter: bool, compressed: bool, skip_technical: bool, remove_adapter: bool, spot_group: bool,
         min_reads: int = None, max_reads: int = None, ar_specific: str = None, ar_start: int = None, ar_end: int = None, member: str = None):
    try:
        run_command_out("vdb-dump --help", dir=sratoolkit_path)
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Setup Incomplete. Please run the setup script again.")
        sys.exit(1)
    working_dir = os.path.join(data_dir, accession)
    set_paths("WORKING_DIR", working_dir)
    os.makedirs(name=working_dir, mode=0o777, exist_ok=True)
    get_data = cmd_for_info(accession=accession)
    download = cmd_to_download(accession, alignment_filter, compressed, skip_technical, remove_adapter, spot_group, alignment_filter_type, min_reads, max_reads, ar_specific, ar_start, ar_end, member)
    print("Fetching data")
    data = run_command_out(get_data, dir=sratoolkit_path)
    print("Downloading Fastq files")
    download_status = run_command_out(download, dir=sratoolkit_path)
    files = []
    for file in list_files_in_directory(working_dir):
        file = os.path.join(working_dir, file)
        files.append(file)
    return data, download_status, files

if __name__ == "__main__":
    accession = "ERR11468775"
    compressed = True
    alignment_filter = False
    alignment_filter_type = None
    skip_technical = False
    remove_adapter = False
    spot_group = False
    min_reads = None
    max_reads = 100
    ar_specific = None
    ar_start = None
    ar_end = None
    member = None
    data, download_status, files = main(accession=accession, alignment_filter=alignment_filter, alignment_filter_type=alignment_filter_type, compressed=compressed,
         skip_technical=skip_technical, remove_adapter=remove_adapter, spot_group=spot_group, min_reads=min_reads, max_reads=max_reads,
         ar_specific=ar_specific, ar_start=ar_start, ar_end=ar_end, member=member)
    print(f"{accession} DATA:\n"+data)
    print("DOWNLOAD STATUS:\n"+download_status)
    for file in files:
        print("SRA FILES: "+file)
