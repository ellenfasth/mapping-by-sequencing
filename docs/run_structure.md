# Template-Based Run Structure

## Before (Scattered):
```
mapping-by-sequencing/
├── results/           # Mixed results from different runs
├── logs/             # Mixed logs from different runs  
├── data/             # Mixed data from different runs
├── config.yaml       # Single config for all runs
└── Snakefile         # Single pipeline file
```

## After (Template-Based):
```
mapping-by-sequencing/
├── templates/                 # Base templates for all runs
│   ├── Snakefile.template    # Pipeline template
│   └── config.yaml.template  # Configuration template
├── scripts/                   # Run generation tools
│   ├── run_manager.py        # Python run manager
│   ├── create_run.sh         # Shell wrapper
│   └── test_reproducibility.sh
├── data/                     # Master data (shared across runs)
│   ├── reads/                # All sequencing data
│   ├── reference_genomes/    # Reference genomes
│   └── datasets.tab          # Master dataset list
├── modules/                   # Shared code (pipeline logic)
├── runs/                      # Generated run folders
│   ├── run_20250115_D3_vs_D2/          # Auto-named run folder
│   │   ├── results/                     # Run-specific results
│   │   │   ├── D2/
│   │   │   ├── D3/
│   │   │   └── final/
│   │   ├── logs/                        # Run-specific logs
│   │   ├── data/                         # Run-specific data (smart symlinks)
│   │   │   ├── reads/                    # Only files needed for this run
│   │   │   ├── reads_filtered/           # Run-specific filtered reads
│   │   │   ├── reference_genomes/        # Symlinks to master references
│   │   │   └── datasets.tab              # Run-specific sample list
│   │   ├── config.yaml                   # Run-specific configuration
│   │   ├── Snakefile                     # Run-specific pipeline (from template)
│   │   └── run_summary.txt               # Run documentation
│   │
│   └── run_20250115_Unknown_vs_D2/      # Another run
│       ├── results/
│       ├── logs/
│       ├── data/
│       └── ...
```

## Benefits:

✅ **Clean separation** - Each run is self-contained  
✅ **Easy comparison** - Compare results between runs  
✅ **Simple cleanup** - Remove entire run folders  
✅ **Reproducibility** - Each run has its own config and data  
✅ **Easy sharing** - Copy entire run folder to share  
✅ **Multiple experiments** - Run different sample combinations simultaneously  
✅ **Storage efficient** - Large data files stay in master location, runs use symlinks  
✅ **Smart data filtering** - Each run gets only the data it needs

## Smart Data Management

**Problem:** Copying all data to each run would waste storage and slow down run creation

**Solution:** Smart symlinks that provide each run with exactly what it needs:

- **Reads**: Only the specific sample files defined in `datasets.tab`
- **Reference Genomes**: Symlinks to master reference files
- **No Duplication**: Large files stay in master location
- **Fast Creation**: Runs created in seconds, not minutes
- **Easy Cleanup**: Remove run folder, no data duplication concerns

**Example:** A run with samples D2 and D3 gets symlinks to only:
- `D2_1.R1.fastq.gz` → `../../data/reads/Unknown_CQ226-001R0001_1.fq.gz`
- `D2_1.R2.fastq.gz` → `../../data/reads/Unknown_CQ226-001R0001_2.fq.gz`
- `D3_1.R1.fastq.gz` → `../../data/reads/Unknown_CQ226-001R0019_1.fq.gz`
- `D3_1.R2.fastq.gz` → `../../data/reads/Unknown_CQ226-001R0019_2.fq.gz`

## Usage:

```bash
# Create new run
./scripts/create_run.sh

# List all runs
python scripts/run_manager.py list

# Clean a run (remove results, keep config)
python scripts/run_manager.py clean --run run_20250115_D3_vs_D2

# Navigate to run and execute
cd runs/run_20250115_D3_vs_D2
snakemake --cores 4
```
