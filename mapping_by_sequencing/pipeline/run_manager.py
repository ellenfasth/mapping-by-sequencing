#!/usr/bin/env python3
"""
Simple Mapping-by-sequencing Pipeline Run Manager

Usage:
    python scripts/run_manager.py configure E1 E19
    python scripts/run_manager.py run run_20250810_E1_vs_E19
    python scripts/run_manager.py list
"""

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import yaml
from typing import Optional


class RunManager:
    def __init__(self):
        # Find the repository root by looking for the data directory
        current_dir = Path.cwd()
        repo_root = None
        
        # Walk up directories to find the one with data/ and templates/ folders
        for parent in [current_dir] + list(current_dir.parents):
            if (parent / "data").exists() and (parent / "templates").exists():
                repo_root = parent
                break
        
        if repo_root is None:
            raise RuntimeError("Could not find repository root (no data/ and templates/ folders found)")
        
        self.repo_root = repo_root
        self.runs_dir = self.repo_root / "runs"
        self.templates_dir = self.repo_root / "templates"
        self.master_data_dir = self.repo_root / "data"
        
        # Create runs directory if it doesn't exist
        self.runs_dir.mkdir(exist_ok=True)
    
    def configure_run(self, control_sample: str, mutant1: str, mutant2: str):
        """Configure a new run: control_sample=control, mutant1=mutated, mutant2=mutated"""
        print(f"🔍 Configuring run: {control_sample} (control) vs {mutant1} (mutant1) vs {mutant2} (mutant2)")
        
        # Load sample mapping
        sample_mapping_file = self.master_data_dir / "sample_mapping.yaml"
        if not sample_mapping_file.exists():
            print("❌ Sample mapping file not found")
            sys.exit(1)
        
        try:
            with open(sample_mapping_file, 'r') as f:
                sample_mapping = yaml.safe_load(f)
            
            # Validate samples exist in mapping
            available_samples = list(sample_mapping.keys())
            
            if control_sample not in available_samples:
                print(f"❌ Control sample '{control_sample}' not found")
                print(f"Available: {', '.join(available_samples)}")
                sys.exit(1)
            
            if mutant1 not in available_samples:
                print(f"❌ Mutant sample 1 '{mutant1}' not found")
                print(f"Available: {', '.join(available_samples)}")
                sys.exit(1)
                
            if mutant2 not in available_samples:
                print(f"❌ Mutant sample 2 '{mutant2}' not found")
                print(f"Available: {', '.join(available_samples)}")
                sys.exit(1)
                
        except Exception as e:
            print(f"❌ Error reading sample mapping: {e}")
            sys.exit(1)
        
        # Generate run name
        run_name = f"run_{datetime.now().strftime('%Y%m%d')}_{control_sample}_vs_{mutant1}_vs_{mutant2}"
        run_dir = self.runs_dir / run_name
        
        if run_dir.exists():
            print(f"❌ Run already exists: {run_name}")
            sys.exit(1)
        
        print(f"📁 Creating run: {run_name}")
        run_dir.mkdir(parents=True)
        
        # Copy Snakefile template
        snakefile_template = self.templates_dir / "Snakefile.template"
        if snakefile_template.exists():
            shutil.copy2(snakefile_template, run_dir / "Snakefile")
            print("📋 Created Snakefile")
        else:
            print("❌ Snakefile template not found")
            sys.exit(1)
        
        # Create run-specific config
        config_template = self.templates_dir / "config.yaml.template"
        if config_template.exists():
            with open(config_template, 'r') as f:
                config = yaml.safe_load(f)
            config['workdir'] = str(run_dir)
            
            with open(run_dir / "config.yaml", 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            print("📝 Created config.yaml")
        else:
            print("❌ Config template not found")
            sys.exit(1)
        
        # Create run-specific datasets.tab using actual sample names (e.g., E1/E19/E20)
        run_datasets = pd.DataFrame({
            'sample': [control_sample, mutant1, mutant2],
            'sample_type': ['control', 'mutated', 'mutated'],
            'library': [1, 1, 1],
            'R1': [
                str(self.repo_root / "data" / "reads" / sample_mapping[control_sample]['R1']),
                str(self.repo_root / "data" / "reads" / sample_mapping[mutant1]['R1']),
                str(self.repo_root / "data" / "reads" / sample_mapping[mutant2]['R1'])
            ],
            'R2': [
                str(self.repo_root / "data" / "reads" / sample_mapping[control_sample]['R2']),
                str(self.repo_root / "data" / "reads" / sample_mapping[mutant1]['R2']),
                str(self.repo_root / "data" / "reads" / sample_mapping[mutant2]['R2'])
            ]
        })

        run_datasets.to_csv(run_dir / "datasets.tab", sep='\t', index=False)
        print(f"📊 Created datasets.tab (control={control_sample}, mutant1={mutant1}, mutant2={mutant2})")
        
        # Create summary
        summary = f"""# Run Summary: {run_name}
Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Samples:
- {control_sample} (control)
- {mutant1} (mutant1)
- {mutant2} (mutant2)

To run: mbs run {run_name}
"""
        
        with open(run_dir / "run_summary.txt", 'w') as f:
            f.write(summary)
        
        print(f"✅ Configured run: {run_name}")
        print(f"🚀 To run: mbs run {run_name}")
    
    def run_pipeline(self, run_name: str, cores: Optional[int] = None):
        """Run the pipeline for a configured run.

        If progress=True, show a simple tqdm progress bar by polling snakemake summaries while the
        workflow is running. This does not slow down the pipeline but provides a task-level view.
        """
        run_dir = self.runs_dir / run_name
        if not run_dir.exists():
            print(f"❌ Run not found: {run_name}")
            return
        
        print(f"🚀 Starting pipeline for: {run_name}")
        print(f"📁 Working directory: {run_dir}")
        
        # Determine cores to use
        max_cores = os.cpu_count() or 1
        selected_cores = cores if cores and cores > 0 else max_cores
        print(f"🔧 Using {selected_cores} cores")
        
        # Invoke snakemake directly; expect the user to have activated the conda env (mbs)
        command_base = ["snakemake"]
        if shutil.which("snakemake") is None:
            print("❌ snakemake not found. Please 'conda activate mbs' and try again.")
            sys.exit(1)

        def run_sm(args: list[str], capture: bool = False):
            if capture:
                return subprocess.run(command_base + args, cwd=run_dir, check=False, capture_output=True, text=True)
            return subprocess.run(command_base + args, cwd=run_dir, check=False)

        # If progress is requested, pre-compute total steps from dryrun
        total_tasks: Optional[int] = None
        bar = None
        try:
            subprocess.run(["snakemake", "--cores", str(selected_cores)], cwd=run_dir, check=True)
            print("✅ Pipeline completed successfully!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Pipeline failed with exit code: {e.returncode}")
            sys.exit(e.returncode)
        except FileNotFoundError:
            print("❌ snakemake not found. Please install and activate the environment")
            sys.exit(1)

    def status(self, run_name: str, detailed: bool = False):
        """Show snakemake summary for a run (quick status)."""
        run_dir = self.runs_dir / run_name
        if not run_dir.exists():
            print(f"❌ Run not found: {run_name}")
            return
        try:
            args = ["snakemake", "--summary"]
            if detailed:
                args = ["snakemake", "--detailed-summary"]
            subprocess.run(args, cwd=run_dir, check=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to fetch status (exit {e.returncode})")
            sys.exit(1)
        except FileNotFoundError:
            print("❌ snakemake not found. Please install and activate the environment")
            sys.exit(1)

    def watch(self, run_name: str, interval_seconds: int = 10, detailed: bool = True):
        """Continuously show status; if tqdm is available, render a simple progress bar.

        Note: Progress is heuristic, based on parsing Snakemake summary output.
        """
        run_dir = self.runs_dir / run_name
        if not run_dir.exists():
            print(f"❌ Run not found: {run_name}")
            return

        # Attempt to estimate total tasks from a dryrun
        total_tasks: Optional[int] = None
        try:
            dry = subprocess.run(["snakemake", "--dryrun"], cwd=run_dir, check=False, capture_output=True, text=True)
            m = re.search(r"total\s+(\d+)\s+steps", dry.stdout, re.IGNORECASE)
            if m:
                total_tasks = int(m.group(1))
        except Exception:
            pass

        print(f"👀 Watching status for {run_name} (refresh {interval_seconds}s)" + (f"; total ~{total_tasks} tasks" if total_tasks else ""))
        bar = None
        try:
            while True:
                args = ["snakemake", "--detailed-summary"] if detailed else ["snakemake", "--summary"]
                res = subprocess.run(args, cwd=run_dir, check=False, capture_output=True, text=True)
                out = res.stdout
                # Parse simple finished/pending counts
                finished = len(re.findall(r"finished", out))
                pending = len(re.findall(r"pending|incomplete|failed", out))
                total = total_tasks or (finished + pending if (finished + pending) > 0 else None)
 
                if total:
                    if bar is None:
                        bar = tqdm(total=total, desc="Pipeline progress", unit="tasks")
                    bar.n = min(finished, total)
                    bar.refresh()
                else:
                    print(f"Status: finished={finished}" + (f" / {total}" if total else "") + (f", pending~{pending}" if pending else ""))

                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            print("\n👋 Stopped watching.")
    
    def list_runs(self):
        """List all configured runs"""
        if not self.runs_dir.exists():
            print("No runs found")
            return
        
        runs = [d for d in self.runs_dir.iterdir() if d.is_dir()]
        if not runs:
            print("No runs found")
            return
        
        print(f"Found {len(runs)} run(s):")
        for run_dir in sorted(runs):
            summary_file = run_dir / "run_summary.txt"
            if summary_file.exists():
                with open(summary_file, 'r') as f:
                    first_line = f.readline().strip()
                    run_name = first_line.replace("# Run Summary: ", "")
            else:
                run_name = run_dir.name
            
            print(f"  📁 {run_name}")


def main():
    parser = argparse.ArgumentParser(
        description="Mapping-by-sequencing Pipeline Run Manager",
        epilog="""
Examples:
  python scripts/run_manager.py configure E1 E19 E20
  python scripts/run_manager.py run run_20250810_E1_vs_E19_vs_E20
  python scripts/run_manager.py list
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Configure command
    configure_parser = subparsers.add_parser('configure', help='Configure new run')
    configure_parser.add_argument('control_sample', help='Control sample (e.g., E1)')
    configure_parser.add_argument('mutant1', help='First mutant sample (e.g., E19)')
    configure_parser.add_argument('mutant2', help='Second mutant sample (e.g., E20)')
    
    # Run command  
    run_parser = subparsers.add_parser('run', help='Run pipeline')
    run_parser.add_argument('run_name', help='Run directory name')
    run_parser.add_argument('--cores', type=int, default=None, help='Number of cores to use (default: all available)')
    # simple interface; additional snakemake flags can be given manually if desired
    
    # List command
    subparsers.add_parser('list', help='List all runs')

    # Status command
    status_parser = subparsers.add_parser('status', help='Show run status (Snakemake summary)')
    status_parser.add_argument('run_name', help='Run directory name')
    status_parser.add_argument('--detailed', action='store_true', help='Show detailed summary')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = RunManager()
    
    if args.command == 'configure':
        manager.configure_run(args.control_sample, args.mutant1, args.mutant2)
    elif args.command == 'run':
        manager.run_pipeline(args.run_name, cores=args.cores)
    elif args.command == 'list':
        manager.list_runs()
    elif args.command == 'status':
        manager.status(args.run_name, detailed=getattr(args, 'detailed', False))


if __name__ == "__main__":
    main()
