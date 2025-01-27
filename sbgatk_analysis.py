import os
from dotenv import load_dotenv
from tools import run_command_out, set_paths

load_dotenv()
data_dir = os.getenv("DATA_DIR")
working_dir = os.getenv("WORKING_DIR")
docker_path = os.getenv("DOCKER_PATH")
gatk_path = os.getenv("GATK_PATH")
bcftools_path = os.getenv("BCFTOOLS_PATH")
samtools_path = os.getenv("SAMTOOLS_PATH")

'''
TO PERFORM OPERATIONS OF SAMTOOLS, BCFTOOLS, AND GATK IN DOCKER CONTAINER
FOLLOWING LINUX COMMANDS NEED TO BE EXECUTED:
wget https://storage.googleapis.com/genomics-public-data/resources/broad/hg38/v0/Homo_sapiens_assembly38.dbsnp138.vcf

wget https://storage.googleapis.com/genomics-public-data/resources/broad/hg38/v0/Homo_sapiens_assembly38.dbsnp138.vcf.idx

ls -lh Homo_sapiens_assembly38.dbsnp138.vcf
ls

CHECK IF THESE FILES ARE PRESENT OR NOT - sample1.sam file and chr18.fasta

vim sample1.sam
:se nowrap
:q

sudo apt-get -y install samtools
samtools view -bo sample1.bam sample1.sam

docker pull broadinstitute/gatk 
docker images 
sudo docker run hello-world 
docker run -it -v data/ hello-world:latest
docker run -it -v $PWD:/data/ broadinstitute/gatk:latest 
exit

RUN IN DOCKER CONTAINER
docker run -it -v $PWD:/data broadinstitute/gatk:latest
cd /data/

gatk AddOrReplaceReadGroups -I sample1.bam -O sample1_withRG.bam -ID 1 -LB lib1 -PL ILLUMINA -PU unit1 -SM sample1

gatk SortSam -I sample1_withRG.bam -O sorted_sample1.bam -SO coordinate

samtools flagstat sorted_sample1.bam

gatk MarkDuplicates -I sorted_sample1.bam -O markedDups.bam -M metrics_duplicates

ls

vim metrics_duplicates

:q

../gatk/gatk CreateSequenceDictionary -R chr18.fa   

samtools faidx chr18.fa

mv 

gatk BaseRecalibrator -I markedDups.bam -R chr18.fa --known-sites Homo_sapiens_assembly38.dbsnp138.vcf -O sample1_recal_data.table

ls

Docker – gatk:latest
cd /data/

../../gatk/gatk ApplyBQSR -R chr17.fa -I markedDups.bam --bqsr-recal-file sample1_recal_data.table -O sample1_recal.bam

samtools index sample1_recal.bam

../../gatk/gatk Mutect2 -I sample1_recal.bam -R chr17.fa -O sample1.vcf.gz

../../gatk/gatk FilterMutectCalls -R chr17.fa -V smple1.vcf.gz -O filtered_sample1.vcf.gz

bcftools view --types indels sample1.vcf.gz >> sample1_indels.vcf

bcftools view --types snps sample1.vcf.gz >> sample1_snps.vcf

bcftools filter -i '%QUAL>50' sample1.vcf.gz

exit

wget https://storage.googleapis.com/genomics-public-data/resources/broad/hg38/v0/hapmap_3.3.hg38.vcf.gz

wget https://storage.googleapis.com/genomics-public-data/resources/broad/hg38/v0/hapmap_3.3.hg38.vcf.gz.tbi

docker

cd /data/

../../gatk/gatk HaplotypeCaller -R chr17.fa -I sample1_recal.bam -O sample1_germline.g.vcf.gz -ERC GVCF

COMBINE ALL 3

gatk GenomicsDBImport -V sample1_germline.g.vcf.gz -V sample2_germline.g.vcf.gz -V sample3_germline.g.vcf.gz --genomicsdb-workspace-path test_db --intervals chr18

../../gatk/gatk GenotypeGVCFs -R chr18.fa -V gendb://test_db -O try_new.vcf.gz

bcftools view --types snps try_new.vcf.gz

'''

def sbgatk_analysis(samfile):
    sbgatk_data_dir = os.path.join(working_dir, 'sbgatk_analysis')
    os.makedirs(sbgatk_data_dir, exist_ok=True)
    
    chr18_ref = os.path.join(data_dir, "chr18.fa")

    dbsnp_vcf = os.path.join(sbgatk_data_dir, "Homo_sapiens_assembly38.dbsnp138.vcf")
    dbsnp_vcf_idx = os.path.join(sbgatk_data_dir, "Homo_sapiens_assembly38.dbsnp138.vcf.idx")
    bam_file = os.path.join(sbgatk_data_dir, "sample1.bam")

    try:
        if not os.path.exists(dbsnp_vcf):
            run_command_out(f"wget https://storage.googleapis.com/genomics-public-data/resources/broad/hg38/v0/Homo_sapiens_assembly38.dbsnp138.vcf -O {dbsnp_vcf}")
        if not os.path.exists(dbsnp_vcf_idx):
            run_command_out(f"wget https://storage.googleapis.com/genomics-public-data/resources/broad/hg38/v0/Homo_sapiens_assembly38.dbsnp138.vcf.idx -O {dbsnp_vcf_idx}")
        if not os.path.exists(bam_file):
            run_command_out(f"samtools view -bo {bam_file} {samfile}")
    
    except Exception as e:
        print(f"An error occurred while downloading dbSNP files: {e}")

    # print("Downloading GATK...")
    # run_command_out("docker pull broadinstitute/gatk")
    # run_command_out("docker images")
    # print("Running GATK docker...")
    #run_command_out(f"docker run -it -v $PWD:/data/ broadinstitute/gatk:latest ")


    # run_command_out(f"docker run -it -v {data_dir}:/data broadinstitute/gatk:latest gatk AddOrReplaceReadGroups -I /data/sample1.bam -O /data/sample1_withRG.bam -ID 1 -LB lib1 -PL ILLUMINA -PU unit1 -SM sample1")
    # run_command_out(f"docker run -it -v {data_dir}:/data broadinstitute/gatk:latest gatk SortSam -I /data/sample1_withRG.bam -O /data/sorted_sample1.bam -SO coordinate")
    # run_command_out(f"docker run -it -v {data_dir}:/data broadinstitute/gatk:latest samtools flagstat /data/sorted_sample1.bam")
    # run_command_out(f"docker run -it -v {data_dir}:/data broadinstitute/gatk:latest gatk MarkDuplicates -I /data/sorted_sample1.bam -O /data/markedDups.bam -M /data/metrics_duplicates")
    # run_command_out(f"docker run -it -v {data_dir}:/data broadinstitute/gatk:latest gatk BaseRecalibrator -I /data/markedDups.bam -R /data/chr18.fa --known-sites /data/Homo_sapiens_assembly38.dbsnp138.vcf -O /data/sample1_recal_data.table")
    # run_command_out(f"docker run -it -v {data_dir}:/data broadinstitute/gatk:latest gatk ApplyBQSR -R /data/chr18.fa -I /data/markedDups.bam --bqsr-recal-file /data/sample1_recal_data.table -O /data/sample1_recal.bam")
    # run_command_out(f"docker run -it -v {data_dir}:/data broadinstitute/gatk:latest samtools index /data/sample1_recal.bam")
    # run_command_out(f"docker run -it -v {data_dir}:/data broadinstitute/gatk:latest gatk Mutect2 -I /data/sample1_recal.bam -R /data/chr18.fa -O /data/sample1.vcf.gz")
    # run_command_out(f"docker run -it -v {data_dir}:/data broadinstitute/gatk:latest gatk FilterMutectCalls -R /data/chr18.fa -V /data/sample1.vcf.gz -O /data/filtered_sample1.vcf.gz")
    # run_command_out(f"docker run -it -v {data_dir}:/data broadinstitute/gatk:latest bcftools view --types indels /data/sample1.vcf.gz >> /data/sample1_indels.vcf")
    # run_command_out(f"docker run -it -v {data_dir}:/data broadinstitute/gatk:latest bcftools view --types snps /data/sample1.vcf.gz >> /data/sample1_snps.vcf")
    # run_command_out(f"docker run -it -v {data_dir}:/data broadinstitute/gatk:latest bcftools filter -i '%QUAL>50' /data/sample1.vcf.gz")


def main(working_dir):
    sbgatk_data_dir = os.path.join(working_dir, 'sbgatk_analysis')
    set_paths("SBGATK_DATA_DIR", sbgatk_data_dir)

    samfile = os.path.join(working_dir, "bwa_index_map", "sample1.sam")

    vcf_file = sbgatk_analysis(samfile)

    return vcf_file

if __name__ == '__main__':
    vcf_files = main(working_dir)
    