# Mapping-by-sequencing

<!-- TOC START min:2 max:5 link:true asterisk:false update:true -->
- [Overview](#overview)
- [Installation](#installation)
- [Set up working environment](#set-up-working-environment)
    - [Install conda environment](#install-conda-environment)
    - [macOS-specific setup](#macos-specific-setup)
    - [Modules to load on Rackham](#modules-to-load-on-rackham)
- [Data preparation](#data-preparation)
    - [Reference genome and snpEff database](#reference-genome-and-snpeff-database)
    - [Sample datasets](#sample-datasets)
- [Running the pipeline](#running-the-pipeline)
    - [Quick start](#quick-start)
    - [Template-based run management](#template-based-run-management)
    - [Advanced usage](#advanced-usage)
- [Output and results](#output-and-results)
- [Reproducibility](#reproducibility)
- [Troubleshooting](#troubleshooting)
<!-- TOC END -->

## Overview

This pipeline is intended to emulate [artMAP](https://github.com/RihaLab/artMAP) and has been built by following the protocol described in the [artMAP paper](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6560221/) (please refer specifically to https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6560221/bin/PLD3-3-e00146-s002.pdf).

**Key Features:**
- **Template-based architecture** for reproducible, organized runs
- **Cross-platform compatibility** (Linux and macOS)
- **Smart data management** with symlinks to avoid duplication
- **Automatic run naming** based on sample configuration
- **Complete run isolation** for easy sharing and archiving

## Installation

Download this repository to your machine:

```bash
git clone https://github.com/domenico-simone/mapping-by-sequencing.git
cd mapping-by-sequencing
```

## Set up working environment

This pipeline relies on several bioinformatics tools:

- **Core pipeline**: snakemake, FastQC, trimmomatic, bwa, samtools, bcftools, bedtools
- **Annotation**: snpEff
- **Python dependencies**: pandas, PyYAML

### Install conda environment

**For all platforms:**

```bash
conda env create -n mbs -f envs/mbs.yaml
conda activate mbs
pip install -e .
```

### Modules to load on Rackham

For UPPMAX/Rackham cluster users:

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
```

## Data preparation

### Reference genome and snpEff database

1. **Place reference genome** in `data/reference_genomes/` (e.g., `myreference-genome.fna`)
2. **Install snpEff database** matching your reference genome
3. **Update configuration** in `templates/config.yaml.template`:

```yaml
ref_genome: "myreference-genome.fna"
snpEff_db: "your_snpeff_database_name"
```

**Example configuration:**
```yaml
results: "results"
map_dir: "map"
log_dir: "logs"
tmp_dir: "/tmp"
workdir: "."
ref_genome: "myreference-genome.fna"
snpEff_db: "Arabidopsis_thaliana"

read_processing:
    trimmomatic:
        options: "-phred33"
        processing_options: "LEADING:3 TRAILING:3 SLIDINGWINDOW:4:15 MINLEN:100"
        java_cmd: "java"
        java_vm_mem: "4G"
        threads: 4
```

### Sample datasets

The system maps samples E1-E26 to actual sequencing files via `data/sample_mapping.yaml`:

```yaml
E1:
  R1: "Unknown_CQ226-001R0001_1.fq.gz"
  R2: "Unknown_CQ226-001R0001_2.fq.gz"
E2:
  R1: "Unknown_CQ226-001R0002_1.fq.gz"
  R2: "Unknown_CQ226-001R0002_2.fq.gz"
...
E26:
  R1: "Unknown_CQ226-001R0026_1.fq.gz"
  R2: "Unknown_CQ226-001R0026_2.fq.gz"
```

**Sample conventions:**
- **E1**: Control sample (sample_type: control)
- **E2-E26**: Mutated samples (sample_type: mutated)
- All files should be placed in `data/reads/`
- Each run compares 1 control sample against 2 mutant samples

## Running the pipeline

### Quick start

1. **Activate environment:**
   ```bash
   conda activate mbs
   ```

2. **Configure a new run** (pick 1 control and 2 mutants to compare):
   ```bash
   mbs configure E1 E19 E20
   ```

3. **Run the pipeline:**
   ```bash
   mbs run run_20250810_E1_vs_E19 --cores 8
   ```

4. **List all runs:**
   ```bash
   mbs list
   ```

### Template-based run management

The pipeline uses a template system for organized, reproducible runs:

**Repository structure:**
```
mapping-by-sequencing/
├── templates/                 # Base templates
│   ├── Snakefile.template    # Pipeline definition
│   └── config.yaml.template  # Configuration template
├── scripts/                   # Run management tools
│   ├── run_manager.py        # Python run manager
│   ├── create_run.sh         # Shell wrapper
│   └── test_reproducibility.sh
├── data/                     # Master data (shared)
│   ├── reads/                # Sequencing data
│   ├── reference_genomes/    # Reference genomes
│   └── datasets.tab          # Sample definitions
├── runs/                     # Generated run folders
└── docs/                     # Documentation
```

**Simple 2-step workflow:**
```bash
# Step 1: Configure run (pick 2 samples)
mbs configure E1 E19

# Step 2: Run pipeline
mbs run run_20250810_E1_vs_E19 --cores 8

# List all runs
mbs list
```

**Simple run naming:**
Runs are automatically named based on:
- **Date**: YYYYMMDD format
- **Sample comparison**: SAMPLE1_vs_SAMPLE2 format

**Examples:**
- `run_20250810_E1_vs_E19` - E1 control vs E19 mutant
- `run_20250810_E2_vs_E20` - E2 vs E20 (two mutants)
- `run_20250810_E5_vs_E15` - E5 vs E15 (two mutants)

### Advanced usage

**Custom run configuration:**
```bash
# Edit run-specific config
cd runs/run_YYYYMMDD_SAMPLES
nano config.yaml

# Run with specific resources
snakemake --cores 8 --resources mem_mb=32000

# Dry run to see what will be executed
snakemake --dryrun --cores 4

# Force re-run specific rules
snakemake --cores 4 --forcerun trimmomatic
```

**Pipeline rules:**
- `fastqc_raw`: Quality control of raw reads
- `trimmomatic`: Read trimming and filtering
- `map`: Read alignment to reference with BWA
- `sam2bam`: SAM to BAM conversion
- `SNP_calling`: SNP/indel detection with bcftools
- `fix_chromosome_names`: Chromosome name correction for snpEff
- `annotate_mutant_specific_SNPs`: Variant annotation with snpEff

## Output and results

After a successful run, your results will be organized in the run directory:

**Run structure:**
```
runs/run_20250810_E1_vs_E19/
├── results/                     # Pipeline outputs
│   ├── E1/                     # Control sample results
│   │   ├── map/                # Alignment files (BAM)
│   │   └── variant_calling/    # Variant calls (VCF)
│   ├── E19/                    # Mutant sample results
│   │   ├── map/                # Alignment files (BAM)
│   │   └── variant_calling/    # Variant calls (VCF)
│   ├── final/                  # Final comparison results
│   └── fastqc_raw/             # Quality control reports
├── logs/                       # Execution logs
├── data/                       # Run-specific read symlinks
├── config.yaml                 # Run configuration
├── Snakefile                   # Pipeline definition
├── datasets.tab                # Run-specific sample mapping
└── run_summary.txt             # Run documentation
```

### Key result files to examine:

**🔬 Main scientific results:**
- `results/final/all_vs_E1_ann.vcf` - **Final annotated variants** (E19 vs E1 comparison)
- `results/final/all_vs_E1_snpEff_summary.html` - **Variant annotation summary** (open in browser)
- `results/final/all_vs_E1_snpEff_genes.txt` - **Affected genes list**

**📊 Individual sample results:**
- `results/E1/variant_calling/E1_filt.vcf` - Control sample variants
- `results/E19/variant_calling/E19_filt.vcf` - Mutant sample variants
- `results/E1/map/E1_OUT-sorted.bam` - Control sample alignment
- `results/E19/map/E19_OUT-sorted.bam` - Mutant sample alignment

**🔍 Quality control:**
- `results/fastqc_raw/E1_1.R1_fastqc.html` - Read quality report for E1
- `results/fastqc_raw/E19_1.R1_fastqc.html` - Read quality report for E19

**📋 Run information:**
- `run_summary.txt` - Overview of the configured run
- `config.yaml` - Pipeline parameters used
- `logs/` - Detailed execution logs for troubleshooting

## Reproducibility

**Ensuring reproducibility:**
1. **Version control**: All templates and scripts are version controlled
2. **Environment isolation**: Conda environments with specific tool versions
3. **Run isolation**: Each run is completely self-contained
4. **Configuration tracking**: All run parameters stored in run-specific config
5. **Data provenance**: Symlinks maintain data source tracking

**Testing reproducibility:**
```bash
# Test pipeline reproducibility
./scripts/test_reproducibility.sh

# Re-run specific run
cd runs/run_YYYYMMDD_SAMPLES
snakemake --cores 4 --rerun-incomplete
```

## Troubleshooting

**Common issues:**

1. **"ERROR_CHROMOSOME_NOT_FOUND" in snpEff:**
   - The pipeline automatically fixes this with the `fix_chromosome_names` rule
   - Ensures RefSeq chromosome names are converted to TAIR format

2. **Environment setup issues:**
   - Ensure conda environment is activated: `conda activate mbs`
   - Pipeline automatically handles platform-specific commands

3. **Memory issues:**
   - Adjust `java_vm_mem` in config.yaml
   - Use `--resources mem_mb=XXXXX` with snakemake

4. **Missing dependencies:**
   - Ensure conda environment is activated: `conda activate mbs`
   - Check tool installation: `which bwa && which samtools`

**Getting help:**
- Check run logs in `runs/run_YYYYMMDD_SAMPLES/logs/`
- Review `run_summary.txt` for run details
- Check `docs/RUNS.md` for detailed run documentation

**Support:**
For issues and questions, please check the documentation in the `docs/` folder or refer to the original artMAP repository.

