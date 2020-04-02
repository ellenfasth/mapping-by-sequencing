# Mapping-by-sequencing

<!-- TOC START min:2 max:5 link:true asterisk:false update:true -->
- [Installation](#installation)
- [Set up working environment](#set-up-working-environment)
    - [Install conda environment](#install-conda-environment)
    - [Modules to load on Rackham](#modules-to-load-on-rackham)
- [Set up a run](#set-up-a-run)
    - [Reference genome and snpEff database](#reference-genome-and-snpeff-database)
    - [Parental (control) dataset and mutated datasets](#parental-control-dataset-and-mutated-datasets)
- [Test](#test)
<!-- TOC END -->

This pipeline is intended to emulate [artMAP](https://github.com/RihaLab/artMAP) and it's been built by following the protocol described in the [artMAP paper](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6560221/) (please refer specifically to https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6560221/bin/PLD3-3-e00146-s002.pdf).

## Installation

Download this repository to your machine

```bash
git clone https://github.com/domenico-simone/mapping-by-sequencing.git 
```

## Set up working environment

This pipeline relies on a bunch of dependencies, namely:

- snakemake
- FastQC
- trimmomatic
- bwa
- samtools
- bcftools
- bedtools
- snpEff

if you already have these tools installed on your system, please skip to the section [Set up a run](#set-up-a-run). If you don't, you can choose one of the following options:

- install them on your own
- install the conda environment provided in the mapping-by-sequencing repository (please follow instructions [here](#install-conda-environment))
- if you are working on the UPPMAX/Rackham cluster, all these tools can be loaded as modules (please follow instructions [here](#modules-to-load-on-rackham))

### Install conda environment

```bash
cd mapping-by-sequencing

conda env create -n mbs -f envs/mbs.yaml
```

This will create a conda environment named `mbs` which has to be activated every time you want to use the pipeline with one of this commands (depending on your conda installation):

```bash
conda activate mbs

# if the above fails, use this:
source activate mbs
```

When you're done with the pipeline, you may want to deactivate the conda environment with:

```bash
conda deactivate
```

### Modules to load on Rackham

These are needed to run the workflow down to SNP calling

```bash
module load bioinfo-tools
module load snakemake
module load FastQC
module load trimmomatic
module load bwa
module load samtools
module load bcftools
module load BEDTools
module load snpEff
# others
```

## Set up a run

### Reference genome and snpEff database

The reference genome in fasta format should be placed in the folder `data/reference_genomes` and its file name has to be detailed in the `config.yaml` file in the `ref_genome` field.  

The snpEff db matching the reference genome should be already installed in snpEff and its name should be detailed in the `config.yaml` file in the `snpEff_db` field.

**Example**: if your reference genome is included in a file `My_ref_genome.fa` and your snpEff database is called `Genus_species`, the `config.yaml` file should look like:

```
results:    "results"
map_dir:    "map"
log_dir:    "logs"
tmp_dir:    "/tmp"
workdir:    "test"
ref_genome: "My_ref_genome.fa"
snpEff_db:  "Genus_species"

read_processing:
    trimmomatic:
        options: "-phred33"
        processing_options: "LEADING:3 TRAILING:3 SLIDINGWINDOW:4:15 MINLEN:100"
        java_cmd: "java"
        java_vm_mem: "4G"
        threads: 4
```

### Parental (control) dataset and mutated datasets

File `data/datasets.tab` should be filled with data about your samples. Its structure is:

```
sample  sample_type  library  R1              R2
D1K     control      1        D1K_L1_1.fq.gz  D1K_L1_2.fq.gz
D2K     mutated      1        D2K_L2_1.fq.gz  D2K_L2_2.fq.gz
D2K     mutated      2        D2K_L3_1.fq.gz  D2K_L3_2.fq.gz
D3K     mutated      1        D3K_L2_1.fq.gz  D3K_L2_2.fq.gz
D4K     mutated      1        D4K_L1_1.fq.gz  D4K_L1_1.fq.gz
D5K     mutated      1        D5K_L2_1.fq.gz  D5K_L2_2.fq.gz
```

where

- **sample** is the sample name
- **sample_type** indicates whether the sample is a control (the parental line) or a mutated line
- **library** takes into account the fact that a sample can have multiple read datasets (libraries). Eg, in the example above, sample D2K has two libraries.
- **R1** and **R2** are the name of the R1 and R2 file for each library, assuming they are located in the directory `data/reads`.

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
