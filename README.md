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
module load BEDTools
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

```bash
sbatch -A snic2018-8-310 -p core -n2 -t 8:00:00 \
-J test -o test_12.out -e test_12.err \
--mail-type=ALL --mail-user=domenico.simone@slu.se<<'EOF'
#!/usr/bin/bash

module load bioinfo-tools
module load FastQC
module load trimmomatic
module load bwa
module load samtools
module load bcftools

snakemake -rp -j 100 --rerun-incomplete results/D1K/variant_calling/D1K.vcf results/D5K/variant_calling/D5K.vcf

EOF
```

```bash
sbatch -A snic2018-8-310 -p core -n12 -t 20:00:00 \
-J test -o test_13.out -e test_13.err \
--mail-type=ALL --mail-user=domenico.simone@slu.se<<'EOF'
#!/usr/bin/bash

module load bioinfo-tools
module load FastQC
module load trimmomatic
module load bwa
module load samtools
module load bcftools

snakemake -rp -j 100 results/D2K/variant_calling/D2K.vcf results/D3K/variant_calling/D3K.vcf results/D4K/variant_calling/D4K.vcf

EOF
```

```bash
sbatch -A snic2018-8-310 -p core -n 4 -t 20:00:00 \
-J test -o test_15.out -e test_15.err \
--mail-type=ALL --mail-user=domenico.simone@slu.se<<'EOF'
#!/usr/bin/bash

module load bioinfo-tools
module load FastQC
module load trimmomatic
module load bwa
module load samtools
module load bcftools

snakemake -rp -j 100 results/D4K/variant_calling/D4K.vcf

EOF
```
