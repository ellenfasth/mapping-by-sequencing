import os
import pandas as pd
from modules.config_parsers import *

configfile: "data/config.yaml"
log_dir = config["log_dir"]

# SAMPLES = ["A", "B", "C"]
# CONTROL = "CTRL"
# ALL = SAMPLES + [CONTROL]

datasets_tab = pd.read_table("data/datasets.tab", sep = "\t", comment='#')
CONTROL, SAMPLES = get_control_samples(datasets_tab)
ALL = SAMPLES + [CONTROL]

wildcard_constraints:
    sample      = '|'.join([re.escape(x) for x in list(set(datasets_tab['sample']))]),
    sample_ctrl = '|'.join([re.escape(x) for x in list(set(datasets_tab['sample']))]),
    #library     = '|'.join([re.escape(x) for x in list(set(datasets_tab['library']))])

rule all:
    input:
        fastqc_raw_outputs(datasets_tab=datasets_tab),
        expand("results/final/all_vs_{ctrl}.vcf", ctrl=CONTROL)
        # mutant_ann_vcf = expand("annotations/{sample}_{ctrl}_ann.vcf", sample=SAMPLES, ctrl=CONTROL),
        # control_filt_vcf = expand("variant_calling/{ctrl}_filt.vcf", ctrl=CONTROL),

rule symlink_libraries:
    input:
        R1 = lambda wildcards: expand(get_datasets_for_symlinks(datasets_tab, sample = wildcards.sample_ctrl, library = wildcards.library, d = "R1")),
        R2 = lambda wildcards: expand(get_datasets_for_symlinks(datasets_tab, sample = wildcards.sample_ctrl, library = wildcards.library, d = "R2"))
    output:
        R1 = "data/reads/{sample_ctrl}_{library}.R1.fastq.gz",
        R2 = "data/reads/{sample_ctrl}_{library}.R2.fastq.gz",
    shell:
        """
        cd data/reads/
        ln -sf $(basename {input.R1}) $(basename {output.R1})
        ln -sf $(basename {input.R2}) $(basename {output.R2})
        """

rule fastqc_raw:
    input:
        R1 = "data/reads/{sample_ctrl}_{library}.R1.fastq.gz",
        R2 = "data/reads/{sample_ctrl}_{library}.R2.fastq.gz",
    output:
        html_report_R1 = "results/fastqc_raw/{sample_ctrl}_{library}.R1_fastqc.html",
        html_report_R2 = "results/fastqc_raw/{sample_ctrl}_{library}.R2_fastqc.html",
    params:
        outDir = "results/fastqc_raw/",
    threads:
        2
    # version:
    #     subprocess.check_output("fastqc -V", shell=True)
    # message:
    #     "QC of raw read files {input} with {version}, {wildcards}"
    log:
        "logs/fastqc_raw/{sample_ctrl}_{library}.log"
    #conda: "envs/environment.yaml"
    shell:
        """
        mkdir -p {params.outDir}
        fastqc -t {threads} -o {params.outDir} {input} &> {log}
        """

rule trimmomatic:
    """ QCing and cleaning reads """
    params:
        java_cmd = config['read_processing']['trimmomatic']['java_cmd'],
        #jar_file = config['read_processing']['trimmomatic']['jar_file'],
        mem = config['read_processing']['trimmomatic']['java_vm_mem'],
        options = config['read_processing']['trimmomatic']['options'],
        processing_options = config['read_processing']['trimmomatic']['processing_options'],
        out1P = "data/reads_filtered/{sample_ctrl}_{library}_qc.R1.fastq.gz",
        out2P = "data/reads_filtered/{sample_ctrl}_{library}_qc.R2.fastq.gz",
        out1U = "data/reads_filtered/{sample_ctrl}_{library}_qc.1U.fastq.gz",
        out2U = "data/reads_filtered/{sample_ctrl}_{library}_qc.2U.fastq.gz"
    input:
        R1 = "data/reads/{sample_ctrl}_{library}.R1.fastq.gz",
        R2 = "data/reads/{sample_ctrl}_{library}.R2.fastq.gz"
    output:
        out1P = "data/reads_filtered/{sample_ctrl}_{library}_qc.R1.fastq.gz",
        out2P = "data/reads_filtered/{sample_ctrl}_{library}_qc.R2.fastq.gz",
        out1U = "data/reads_filtered/{sample_ctrl}_{library}_qc.U.fastq.gz",
    threads:
        config['read_processing']['trimmomatic']['threads']
    # version:
    #     subprocess.check_output("trimmomatic -version", shell=True)
    message:
        "Filtering read dataset {wildcards.sample_ctrl}_{wildcards.library} with Trimmomatic. {wildcards}" # v{version}"
    log:
        log_dir + "/trimmomatic/{sample_ctrl}_{library}_trimmomatic.log"
    #conda: "envs/environment.yaml"
    run:
        #trimmomatic_adapters_path = get_trimmomatic_adapters_path()
        shell("export tap=$(which trimmomatic | sed 's/bin\/trimmomatic/share\/trimmomatic\/adapters\/TruSeq3-PE.fa/g'); trimmomatic PE {params.options} -threads {threads} {input.R1} {input.R2} {params.out1P} {params.out1U} {params.out2P} {params.out2U} ILLUMINACLIP:$tap:2:30:10 {params.processing_options} &> {log}")
        shell("zcat {params.out1U} {params.out2U} | gzip > {output.out1U} && rm {params.out1U} {params.out2U}")

rule map:
    input:
        f1 = "data/reads_filtered/{sample_ctrl}_{library}_qc.R1.fastq.gz",
        f2 = "data/reads_filtered/{sample_ctrl}_{library}_qc.R2.fastq.gz"
        # f1 = expand("data/filtered/{sample_ctrl}.R1.fastq.gz", sample_ctrl=ALL),
        # f2 = expand("data/filtered/{sample_ctrl}.R2.fastq.gz", sample_ctrl=ALL)
    output:
        temp(sam = "results/{sample_ctrl}/map/OUT_{sample_ctrl}_{library}/{sample}_{library}_OUT.sam.gz")
        #sam = "results/{sample_ctrl}_{library}/map/{sample_ctrl}_{library}.sam"
    # params:
    #     bwa_index = lambda wildcards, input: 
    run:
        shell("bwa mem {params.bwa_index} {input.f1} {input.f2}")

rule sam2bam:
    input:
        sam = "results/{sample_ctrl}/map/OUT_{sample_ctrl}_{library}/{sample_ctrl}_{library}_OUT.sam.gz"
#        sam = "alignment/{sample_ctrl}_{library}.sam"
    output:
        bam = temp("results/{sample_ctrl}/map/OUT_{sample_ctrl}_{library}/{sample_ctrl}_{library}_OUT-sorted.bam")
    params:
        TMP = check_tmp_dir("/tmp"),
        first_bam  = lambda wildcards: os.path.join(check_tmp_dir("/tmp"), "{}.bam".format(wildcards.sample_ctrl)),
        sorted_bam = lambda wildcards: os.path.join(check_tmp_dir("/tmp"), "{}.sorted.bam".format(wildcards.sample_ctrl))
    run:
        shell("samtools view -bS -o {params.TMP}/{params.first_bam} {input.sam}")
        shell("samtools sort -T {params.TMP}/{wildcards.sample_ctrl} -o {params.TMP}/{params.sorted_bam} {params.first_bam}")
        shell("samtools rmdup -s {output.bam} {params.sorted_bam}")

rule merge_bam:
    input:
        sorted_bams = lambda wildcards: get_sample_bamfiles(datasets_tab, res_dir="results", sample = wildcards.sample_ctrl)
    output:
        merged_bam = "results/{sample_ctrl}/map/{sample_ctrl}_OUT-sorted.bam",
        merged_bam_index = "results/{sample_ctrl}/map/{sample_ctrl}_OUT-sorted.bam.bai"
    log: log_dir + "/{sample_ctrl}/{sample_ctrl}_merge_bam.log"
    #conda: "envs/samtools_biopython.yaml"
    shell:
        """
        samtools merge {output.merged_bam} {input} &> {log}
        samtools index {output.merged_bam} {output.merged_bam_index}
        """

rule SNP_calling:
    input:
        bam = "results/{sample_ctrl}/map/{sample_ctrl}_OUT-sorted.bam"
    output:
        vcf = "results/{sample_ctrl}/variant_calling/{sample_ctrl}.vcf"
    params:
        ref = "ARABIDOPSIS_REF.fa"
    run:
        shell("samtools mpileup -Q 30 -C 50 -P Illumina \
                -t DP,DV,INFO/DPR,DP4,SP,DV \
                -Buf {params.ref} {input.bam} \
                | bcftools view -vcg --types snps > {output.vcf}")

rule filter_SNPs:
    input:
        vcf = "results/{sample_ctrl}/variant_calling/{sample_ctrl}.vcf"
    output:
        vcf = "results/{sample_ctrl}/variant_calling/{sample_ctrl}_filt.vcf"
    run:
        shell("# murt d l inhouse script")

rule get_mutant_specific_SNPs:
    input:
        mutant_snps  = expand("results/{sample}/variant_calling/{sample}_filt.vcf", sample=SAMPLES),
        control_snps = expand("results/{ctrl}/variant_calling/{ctrl}_filt.vcf", ctrl=CONTROL)
    output:
        vcf = "results/{sample}/variant_calling/{sample}_{ctrl}_filt.vcf"
    run:
        shell("subtractBed -a {input.mutant_snps} -b {input.control_snps} > {output.vcf}")

rule merge_mutant_specific_SNPs:
    input:
        vcf = expand("results/{sample}/variant_calling/{sample}_{ctrl}_filt.vcf", sample=SAMPLES, ctrl=CONTROL)
    output:
        vcf = "results/final/all_vs_{ctrl}.vcf"
    run:
        shell("bcftools merge {input.single_vcf_list} -O v -o {output.merged_vcf}")

rule annotate_mutant_specific_SNPs:
    input:
        vcf = "results/final/all_vs_{ctrl}.vcf"
    output:
        vcf = "results/final/all_vs_{ctrl}_ann.vcf"
    run:
        shell("snpEff Arabidopsis_thaliana {input.vcf}")
