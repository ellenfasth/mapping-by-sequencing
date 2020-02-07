import os

def check_tmp_dir(dir):
    if os.getenv("TMP"):
        TMP = os.getenv("TMP")
    else:
        TMP = dir
    return TMP

SAMPLES = ["A", "B", "C"]
CONTROL = "CTRL"
ALL = SAMPLES + [CONTROL]

rule all:
    input:
        mutant_ann_vcf = expand("annotations/{sample}_{ctrl}_ann.vcf", sample=SAMPLES, ctrl=CONTROL),
        control_filt_vcf = expand("variant_calling/{ctrl}_filt.vcf", ctrl=CONTROL)
# 
# rule symlink_libraries:
#     input:
#         R1 = lambda wildcards: get_datasets_for_symlinks(datasets_tab, sample = wildcards.sample, library = wildcards.library, d = "R1"),
#         R2 = lambda wildcards: get_datasets_for_symlinks(datasets_tab, sample = wildcards.sample, library = wildcards.library, d = "R2")
#     output:
#         R1 = "data/reads/{sample}_{library}.R1.fastq.gz",
#         R2 = "data/reads/{sample}_{library}.R2.fastq.gz",
#     shell:
#         """
#         cd data/reads/
#         ln -sf $(basename {input.R1}) $(basename {output.R1})
#         ln -sf $(basename {input.R2}) $(basename {output.R2})
#         """

rule map:
    input:
        f1 = expand("data/filtered/{sample_ctrl}_1.fastq.gz", sample_ctrl=ALL),
        f2 = expand("data/filtered/{sample_ctrl}_2.fastq.gz", sample_ctrl=ALL)
    output:
        sam = "alignment/{sample_ctrl}.sam"
    # params:
    #     bwa_index = lambda wildcards, input: 
    run:
        shell("bwa mem {params.bwa_index} {input.f1} {input.f2}")

rule sam2bam:
    input:
        sam = "alignment/{sample_ctrl}.sam"
    output:
        bam = "alignment/{sample_ctrl}.bam"
    params:
        TMP = check_tmp_dir("/tmp"),
        first_bam  = lambda wildcards: os.path.join(check_tmp_dir("/tmp"), "{}.bam".format(wildcards.sample_ctrl)),
        sorted_bam = lambda wildcards: os.path.join(check_tmp_dir("/tmp"), "{}.sorted.bam".format(wildcards.sample_ctrl))
    run:
        shell("samtools view -bS -o {params.first_bam} {input.sam}")
        shell("samtools sort -T {params.TMP}/{wildcards.sample_ctrl} -o {params.sorted_bam} {params.first_bam}")
        shell("samtools rmdup -s {output.bam} {params.sorted_bam}")
        
rule SNP_calling:
    input:
        bam = "alignment/{sample_ctrl}.bam"
    output:
        vcf = "variant_calling/{sample_ctrl}.vcf"
    params:
        ref = "ARABIDOPSIS_REF.fa"
    run:
        shell("samtools mpileup -Q 30 -C 50 -P Illumina \
                -t DP,DV,INFO/DPR,DP4,SP,DV \
                -Buf {params.ref} {input.bam} \
                | bcftools view -vcg --types snps > {output.vcf}")

rule filter_SNPs:
    input:
        vcf = "variant_calling/{sample_ctrl}.vcf"
    output:
        vcf = "variant_calling/{sample_ctrl}_filt.vcf"
    run:
        shell("# murt d l inhouse script")

rule get_mutant_specific_SNPs:
    input:
        mutant_snps  = expand("variant_calling/{sample}_filt.vcf", sample=SAMPLES),
        control_snps = expand("variant_calling/{ctrl}_filt.vcf", ctrl=CONTROL)
    output:
        vcf = "variant_calling/{sample}_{ctrl}_filt.vcf"
    run:
        shell("subtractBed -a {input.mutant_snps} -b {input.control_snps} > {output.vcf}")


rule annotate_mutant_specific_SNPs:
    input:
        vcf = "variant_calling/{sample}_{ctrl}_filt.vcf"
    output:
        vcf = "annotations/{sample}_{ctrl}_ann.vcf"
    run:
        shell("snpEff Arabidopsis_thaliana {input.vcf}")
