# Mapping-by-sequencing

Mapping by sequencing pipeline

## Modules to load on Rackham

These are needed to run the workflow down to SNP calling

```bash
module load bioinfo-tools
module load FastQC
module load trimmomatic
module load bwa
module load samtools
module load bcftools
# others
```

## Test

```bash
snakemake -C workdir=test -nrp
```

```bash
snakemake -nrp results/D1K/map/D1K_OUT-sorted.bam results/D5K/map/D5K_OUT-sorted.bam
```

```bash
snakemake -nrp results/D1K/variant_calling/D1K.vcf results/D5K/variant_calling/D5K.vcf &> test_10.log &
```
