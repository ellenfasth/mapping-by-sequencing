SAMPLES = ["A", "B", "C"]
CONTROL = "CTRL"

rule all:
    input:
        ann_vcf = expand("annotations/{sample}_ann.vcf", sample=SAMPLES.append(CONTROL))

rule SNP_filtering:


rule get_mutant_specific_SNPs:
    input:
        
    output:
        vcf = "variant_calling/{sample}_filt.vcf"
    run:
        shell("subtractBed -a ")


rule annotate_mutant_specific_SNPs:
    input:
        vcf = "variant_calling/{sample}_filt.vcf"
    output:
        vcf = "annotations/{sample}_ann.vcf"
    run:
        shell("snpEff Arabidopsis_thaliana {input.vcf}")
