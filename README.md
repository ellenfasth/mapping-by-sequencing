# Mapping-by-sequencing

Mapping by sequencing pipeline

## Modules to load on Rackham

These are needed to run the workflow down to SNP calling

```bash
module load bioinfo-tools
module load fastqc
module load trimmomatic
module load bwa
module load samtools
# others
```

## Test

```bash
snakemake -C workdir=test -nrp
```