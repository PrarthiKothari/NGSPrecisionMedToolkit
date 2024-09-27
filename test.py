file = 'ERR11468775_2_fastqc.html'

newfile = file.strip('.html').replace("_fastqc", ".fastq.gz")
print(newfile)