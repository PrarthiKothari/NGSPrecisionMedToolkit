import os
import subprocess
import time
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()
data_dir = os.getenv("DATA_DIR")
working_dir = os.getenv("WORKING_DIR")

if not data_dir or not working_dir:
    raise EnvironmentError("DATA_DIR and WORKING_DIR must be set in your environment.")

def run_command(command, error_message):
    """
    Helper function to run a shell command with error handling.
    """
    try:
        print(f"\n[Running] {command}")
        result = subprocess.run(command, shell=True, check=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"\n[Error] {error_message}")
        print(f"Command: {command}")
        print(f"Error output: {e.stderr}")
        raise

def sbgatk_analysis(samfile):
    # Create the analysis output folder (inside DATA_DIR)
    analysis_dir = os.path.join(data_dir, 'SBGATK_ANALYSIS')
    os.makedirs(analysis_dir, exist_ok=True)
    print(f"Analysis output will be stored in: {analysis_dir}")

    # Check for the required reference file (chr18.fa)
    chr18_ref = os.path.join(data_dir, "chr18.fa")
    if not os.path.exists(chr18_ref):
        raise FileNotFoundError(f"Reference file {chr18_ref} not found. Please place chr18.fa in {data_dir}.")

    # --------------------------
    # Download Required Files
    # --------------------------
    # Download dbSNP VCF and index
    dbsnp_vcf = os.path.join(analysis_dir, "Homo_sapiens_assembly38.dbsnp138.vcf")
    dbsnp_vcf_idx = os.path.join(analysis_dir, "Homo_sapiens_assembly38.dbsnp138.vcf.idx")
    try:
        if not os.path.exists(dbsnp_vcf):
            run_command(f"wget https://storage.googleapis.com/genomics-public-data/resources/broad/hg38/v0/Homo_sapiens_assembly38.dbsnp138.vcf -O {dbsnp_vcf}",
                        "Failed to download Homo_sapiens_assembly38.dbsnp138.vcf")
        else:
            print("dbSNP VCF already exists.")
        if not os.path.exists(dbsnp_vcf_idx):
            run_command(f"wget https://storage.googleapis.com/genomics-public-data/resources/broad/hg38/v0/Homo_sapiens_assembly38.dbsnp138.vcf.idx -O {dbsnp_vcf_idx}",
                        "Failed to download Homo_sapiens_assembly38.dbsnp138.vcf.idx")
        else:
            print("dbSNP VCF index already exists.")
    except Exception as e:
        print(e)
        return

    # Download hapmap files (if needed)
    hapmap_vcf = os.path.join(analysis_dir, "hapmap_3.3.hg38.vcf.gz")
    hapmap_vcf_tbi = os.path.join(analysis_dir, "hapmap_3.3.hg38.vcf.gz.tbi")
    try:
        if not os.path.exists(hapmap_vcf):
            run_command(f"wget https://storage.googleapis.com/genomics-public-data/resources/broad/hg38/v0/hapmap_3.3.hg38.vcf.gz -O {hapmap_vcf}",
                        "Failed to download hapmap_3.3.hg38.vcf.gz")
        else:
            print("hapmap VCF already exists.")
        if not os.path.exists(hapmap_vcf_tbi):
            run_command(f"wget https://storage.googleapis.com/genomics-public-data/resources/broad/hg38/v0/hapmap_3.3.hg38.vcf.gz.tbi -O {hapmap_vcf_tbi}",
                        "Failed to download hapmap_3.3.hg38.vcf.gz.tbi")
        else:
            print("hapmap VCF index already exists.")
    except Exception as e:
        print(e)
        return

    # --------------------------
    # Prepare Input BAM File
    # --------------------------
    sample_bam = os.path.join(analysis_dir, "sample1.bam")
    if not os.path.exists(sample_bam):
        if not os.path.exists(samfile):
            raise FileNotFoundError(f"Input SAM file {samfile} not found.")
        try:
            run_command(f"samtools view -bo {sample_bam} {samfile}",
                        "Failed to convert SAM to BAM")
        except Exception as e:
            print(e)
            return
    else:
        print("sample1.bam already exists.")

    # --------------------------
    # Create the Bash Script for Analysis
    # --------------------------
    script_path = os.path.join(analysis_dir, "run_analysis.sh")
    try:
        with open(script_path, "w") as f:
            f.write("#!/bin/bash\n")
            f.write("set -e\n")
            # Change directory to where the analysis files are mounted (inside the container /data/SBGATK_ANALYSIS)
            f.write("cd /data/SBGATK_ANALYSIS\n\n")
            f.write("echo 'Running AddOrReplaceReadGroups'\n")
            f.write("gatk AddOrReplaceReadGroups -I sample1.bam -O sample1_withRG.bam -ID 1 -LB lib1 -PL ILLUMINA -PU unit1 -SM sample1\n\n")
            
            f.write("echo 'Running SortSam'\n")
            f.write("gatk SortSam -I sample1_withRG.bam -O sorted_sample1.bam -SO coordinate\n\n")
            
            f.write("echo 'Running samtools flagstat'\n")
            f.write("samtools flagstat sorted_sample1.bam > sorted_sample1_flagstat.txt\n\n")
            
            f.write("echo 'Running MarkDuplicates'\n")
            f.write("gatk MarkDuplicates -I sorted_sample1.bam -O markedDups.bam -M metrics_duplicates.txt\n\n")
            
            f.write("echo 'Listing current files'\n")
            f.write("ls -l\n\n")
            
            f.write("echo 'Creating sequence dictionary (if not already present)'\n")
            f.write("if [ ! -f chr18.dict ]; then gatk CreateSequenceDictionary -R chr18.fa; fi\n\n")
            
            f.write("echo 'Indexing chr18.fa with samtools faidx'\n")
            f.write("samtools faidx chr18.fa\n\n")
            
            f.write("echo 'Running BaseRecalibrator'\n")
            f.write("gatk BaseRecalibrator -I markedDups.bam -R chr18.fa --known-sites Homo_sapiens_assembly38.dbsnp138.vcf -O sample1_recal_data.table\n\n")
            
            f.write("echo 'Applying BQSR'\n")
            f.write("gatk ApplyBQSR -R chr18.fa -I markedDups.bam --bqsr-recal-file sample1_recal_data.table -O sample1_recal.bam\n\n")
            
            f.write("echo 'Indexing recalibrated BAM'\n")
            f.write("samtools index sample1_recal.bam\n\n")
            
            f.write("echo 'Running Mutect2'\n")
            f.write("gatk Mutect2 -I sample1_recal.bam -R chr18.fa -O sample1.vcf.gz\n\n")
            
            f.write("echo 'Filtering Mutect calls'\n")
            f.write("gatk FilterMutectCalls -R chr18.fa -V sample1.vcf.gz -O filtered_sample1.vcf.gz\n\n")
            
            f.write("echo 'Extracting indels with bcftools'\n")
            f.write("bcftools view --types indels sample1.vcf.gz > sample1_indels.vcf\n\n")
            
            f.write("echo 'Extracting SNPs with bcftools'\n")
            f.write("bcftools view --types snps sample1.vcf.gz > sample1_snps.vcf\n\n")
            
            f.write("echo 'Filtering variants with QUAL>50'\n")
            f.write("bcftools filter -i '%QUAL>50' sample1.vcf.gz -o sample1_filtered.vcf\n\n")
            
            f.write("echo 'Running HaplotypeCaller for germline GVCF'\n")
            f.write("gatk HaplotypeCaller -R chr18.fa -I sample1_recal.bam -O sample1_germline.g.vcf.gz -ERC GVCF\n\n")
            
            # For demonstration purposes, if sample2/3 do not exist, copy sample1_germline.g.vcf.gz
            f.write("if [ ! -f sample2_germline.g.vcf.gz ]; then cp sample1_germline.g.vcf.gz sample2_germline.g.vcf.gz; fi\n")
            f.write("if [ ! -f sample3_germline.g.vcf.gz ]; then cp sample1_germline.g.vcf.gz sample3_germline.g.vcf.gz; fi\n\n")
            
            f.write("echo 'Combining gVCF files with GenomicsDBImport'\n")
            f.write("gatk GenomicsDBImport -V sample1_germline.g.vcf.gz -V sample2_germline.g.vcf.gz -V sample3_germline.g.vcf.gz --genomicsdb-workspace-path test_db --intervals chr18\n\n")
            
            f.write("echo 'Genotyping GVCFs'\n")
            f.write("gatk GenotypeGVCFs -R chr18.fa -V gendb://test_db -O try_new.vcf.gz\n\n")
            
            f.write("echo 'Extracting SNPs from combined VCF'\n")
            f.write("bcftools view --types snps try_new.vcf.gz > try_new_snps.vcf\n\n")
            
            f.write("echo 'GATK Analysis Completed'\n")
        os.chmod(script_path, 0o755)
        print(f"Bash script for analysis created at: {script_path}")
    except Exception as e:
        print(f"Error creating bash script: {e}")
        return

    # --------------------------
    # Pull the GATK Docker Image
    # --------------------------
    try:
        run_command("docker pull broadinstitute/gatk:latest", "Failed to pull the GATK Docker image")
    except Exception as e:
        print(e)
        return

    # --------------------------
    # Run the Analysis Script inside Docker
    # --------------------------
    # The container mounts the DATA_DIR as /data so that /data/SBGATK_ANALYSIS contains our files.
    docker_cmd = (f"docker run --rm -v {data_dir}:/data broadinstitute/gatk:latest "
                  f"/bin/bash /data/SBGATK_ANALYSIS/run_analysis.sh")
    try:
        run_command(docker_cmd, "Failed to run the analysis script in the Docker container")
    except Exception as e:
        print(e)
        return

    print("\nGATK analysis completed successfully. Check the SBGATK_ANALYSIS directory for output files.")

def main():
    # Assume the input SAM file is located in WORKING_DIR/bwa_index_map/sample1.sam
    samfile = os.path.join(working_dir, "bwa_index_map", "sample1.sam")
    if not os.path.exists(samfile):
        raise FileNotFoundError(f"Input SAM file {samfile} not found. Please check your WORKING_DIR path.")
    sbgatk_analysis(samfile)

if __name__ == '__main__':
    main()
