# RUNS.md - Mapping-by-sequencing Pipeline Runs

This document tracks pipeline runs, issues, and solutions.

## NEW: Simplified 2-Step Run Management System

The pipeline now uses a simple 2-step process for managing runs:

### Step 1: Configure Run
Create a run directory comparing exactly 2 samples (e.g., E1 vs E19):

```bash
# Using Python script directly
python scripts/run_manager.py configure E1 E19

# Using shell script
./scripts/create_run.sh --sample1 E1 --sample2 E19

# With custom run name
python scripts/run_manager.py configure E1 E19 --name my_experiment
```

**What this does:**
- Creates a run directory (e.g., `run_20250810_E1_vs_E19`)
- Copies Snakefile template and creates run-specific config
- Creates run-specific `datasets.tab` with only the 2 selected samples
- Generates run summary documentation
- **Data stays outside** - no copying of large files

### Step 2: Run Pipeline
Execute the pipeline on the configured run:

```bash
# Run with default 4 cores
python scripts/run_manager.py run --run run_20250810_E1_vs_E19

# Run with custom number of cores
python scripts/run_manager.py run --run run_20250810_E1_vs_E19 --cores 8
```

**What this does:**
- Changes to the run directory
- Executes `snakemake --cores N`
- Creates `results/` and `logs/` directories
- All outputs are contained within the run folder

## Repository Structure

```
mapping-by-sequencing/
├── templates/                    # Templates for new runs
│   ├── Snakefile.template       # Base pipeline definition
│   └── config.yaml.template     # Base configuration
├── scripts/                      # Management scripts
│   ├── run_manager.py           # Main run management script
│   ├── create_run.sh            # Convenience shell script
│   └── test_reproducibility.sh  # Reproducibility testing
├── data/                         # Master data (shared across runs)
│   ├── datasets.tab             # All available samples (E1-E26)
│   ├── reads/                   # Raw sequencing data
│   └── reference_genomes/       # Reference genome files
├── runs/                         # Individual run directories
│   ├── run_20250810_E1_vs_E19/ # Example run
│   └── run_20250810_E2_vs_E20/ # Another example run
├── modules/                      # Core pipeline modules
└── docs/                        # Documentation
```

## Available Samples

The system currently has 26 samples available (E1-E26):
- **E1**: Control sample
- **E2-E26**: Mutated samples (EMS mutagenesis)

Each run compares 1 control sample against 2 mutant samples for comprehensive analysis.

Each sample corresponds to specific read files:
- E1 → `Unknown_CQ226-001R0001_1.fq.gz` / `Unknown_CQ226-001R0001_2.fq.gz`
- E2 → `Unknown_CQ226-001R0002_1.fq.gz` / `Unknown_CQ226-001R0002_2.fq.gz`
- ...and so on

## Run Directory Structure

Each run directory contains:
```
run_YYYYMMDD_CONTROL_vs_MUTANT1_vs_MUTANT2/
├── Snakefile              # Run-specific pipeline definition
├── config.yaml            # Run-specific configuration
├── data/
│   └── datasets.tab      # Run-specific sample configuration (1 control + 2 mutants)
├── run_summary.txt        # Run documentation
├── results/               # Pipeline outputs (created during execution)
└── logs/                  # Execution logs (created during execution)
```

## Key Benefits

- **Simple workflow**: Just 2 commands to go from samples to results
- **No data duplication**: Large files stay in master location
- **Run isolation**: Each run is completely self-contained
- **Easy comparison**: Compare different sample pairs easily
- **Reproducible**: Each run has its own config and data specification

## Usage Examples

### Example 1: E1 vs E19 vs E20 (Control vs Two Mutants)
```bash
# Configure
python scripts/run_manager.py configure E1 E19 E20

# Run
python scripts/run_manager.py run --run run_20250810_E1_vs_E19_vs_E20
```

### Example 2: E1 vs E2 vs E3 (Control vs Two Different Mutants)
```bash
# Configure
python scripts/run_manager.py configure E1 E2 E3

# Run
python scripts/run_manager.py run --run run_20250810_E2_vs_E20
```

### Example 3: Custom Run Name
```bash
# Configure with custom name
python scripts/run_manager.py configure E5 E15 --name "high_impact_mutants"

# Run
python scripts/run_manager.py run --run high_impact_mutants
```

## Management Commands

```bash
# List all runs
python scripts/run_manager.py list

# Clean a run (remove results, keep config)
python scripts/run_manager.py clean --run run_20250810_E1_vs_E19

# Get help
python scripts/run_manager.py --help
```

## Previous Issues and Solutions

### Issue 1: snpEff Chromosome Naming Mismatch
**Problem**: `snpEff` was failing with "ERROR_CHROMOSOME_NOT_FOUND" because RefSeq chromosome names didn't match TAIR format.

**Solution**: Added `rule fix_chromosome_names` to automatically convert RefSeq chromosome names to TAIR format before annotation.

**Files Modified**: 
- `templates/Snakefile.template` - Added chromosome name fixing rule
- `templates/config.yaml.template` - Updated to include chromosome mapping

### Issue 2: Results Scattered Across Repository
**Problem**: Pipeline outputs were scattered across the main repository, making it hard to track which results belong to which run.

**Solution**: Implemented organized run management system where each run has its own isolated directory with all outputs contained within.

### Issue 3: Complex Run Setup Process
**Problem**: Previous system required specifying many parameters and copying large data files.

**Solution**: Simplified to 2-step process: configure (pick 2 samples) and run (execute pipeline).

## Future Improvements

- Add support for batch processing multiple sample pairs
- Implement run comparison tools
- Add quality control metrics to run summaries
- Create run templates for common experimental designs
