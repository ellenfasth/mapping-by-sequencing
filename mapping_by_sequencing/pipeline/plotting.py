"""
Plotting utilities for mapping-by-sequencing results.
"""

import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for headless environments
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
from pathlib import Path
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)

def _detect_sample_columns(header_line: str) -> List[str]:
    """Return list of sample column names from a VCF header line starting with '#CHROM'."""
    parts = header_line.strip().split('\t')
    # Standard VCF has 9 fixed columns; samples start at index 9
    if len(parts) <= 9:
        return []
    return parts[9:]


def parse_vcf_frequency(vcf_file: str, control_sample: Optional[str] = None, min_dp: int = 0):
    """
    Parse VCF file to extract mutation frequency and chromosome location.
    
    Args:
        vcf_file (str): Path to VCF file
        
    Returns:
        dict: Dictionary with chromosome as key and list of (position, frequency) tuples as value
    """
    mutations = defaultdict(list)
    sample_names: Optional[List[str]] = None
    mutant_sample_indices: Optional[List[int]] = None
    
    try:
        with open(vcf_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                if line.startswith('#'):
                    # Capture sample names when we hit the header
                    if line.startswith('#CHROM'):
                        sample_names = _detect_sample_columns(line)
                        if sample_names:
                            # Determine mutant sample indices (0-based relative to samples)
                            if control_sample:
                                mutant_sample_indices = [i for i, name in enumerate(sample_names)
                                                         if control_sample not in name]
                            else:
                                mutant_sample_indices = list(range(len(sample_names)))
                    continue
                    
                parts = line.strip().split('\t')
                if len(parts) < 10:
                    logger.warning(f"Line {line_num}: insufficient columns, skipping")
                    continue
                    
                chrom = parts[0]
                pos = int(parts[1])
                
                # Skip if no samples present
                if len(parts) < 10:
                    continue

                # Parse genotype information to get frequency from mutant samples (exclude control)
                format_fields = parts[8].split(':')
                # Identify indices to consider
                if mutant_sample_indices is None:
                    # If we have not seen header, assume all sample columns are mutants
                    num_samples = len(parts) - 9
                    mutant_sample_indices = list(range(num_samples))

                per_sample_freqs: list[float] = []

                for rel_idx in mutant_sample_indices:
                    col_idx = 9 + rel_idx
                    if col_idx >= len(parts):
                        continue
                    sample_field_str = parts[col_idx]
                    if sample_field_str == '.' or sample_field_str == './.':
                        continue
                    sample_fields = sample_field_str.split(':')

                    # Build dict of FORMAT -> value
                    fmt_map = {key: sample_fields[i] if i < len(sample_fields) else None for i, key in enumerate(format_fields)}

                    # Require an ALT genotype (exclude 0/0), so values from mutants without the variant don't drag the average
                    gt_raw = fmt_map.get('GT') or ''
                    if '1' not in gt_raw:  # handles 0/1, 1/1, 1|0, 1|1, 0/1/2, etc.
                        continue

                    # Prefer AD for allele depths
                    ad_raw = fmt_map.get('AD')
                    dp_raw = fmt_map.get('DP')
                    if not ad_raw:
                        # Try reconstruct from ADF/ADR if available
                        adf_raw = fmt_map.get('ADF')
                        adr_raw = fmt_map.get('ADR')
                        if adf_raw and adr_raw:
                            try:
                                adf = [int(x) for x in adf_raw.split(',') if x != '.']
                                adr = [int(x) for x in adr_raw.split(',') if x != '.']
                                ad_list = [a + b for a, b in zip(adf, adr)]
                                ad_raw = ','.join(str(x) for x in ad_list)
                            except Exception:
                                ad_raw = None
                    if not ad_raw:
                        continue
                    try:
                        ad_vals = [int(x) for x in ad_raw.split(',') if x != '.']
                        if len(ad_vals) < 2:
                            continue
                        ref_depth = ad_vals[0]
                        alt_depth = sum(ad_vals[1:])  # support multi-allelic
                        total_depth = ref_depth + alt_depth
                        # Fallback to DP if AD seems inconsistent
                        if (dp_raw and dp_raw != '.' and dp_raw.isdigit() and int(dp_raw) > total_depth):
                            total_depth = int(dp_raw)
                        if total_depth < max(1, min_dp):
                            continue
                        freq = alt_depth / total_depth
                        per_sample_freqs.append(freq)
                    except Exception:
                        logger.debug(f"Line {line_num}: could not parse AD/DP fields for sample idx {rel_idx}, skipping")
                        continue

                if per_sample_freqs:
                    frequency_pct = float(np.mean(per_sample_freqs)) * 100.0
                    mutations[chrom].append((pos, frequency_pct))
                    
    except FileNotFoundError:
        logger.error(f"VCF file not found: {vcf_file}")
        raise
    except Exception as e:
        logger.error(f"Error parsing VCF file: {e}")
        raise
    
    return mutations

def create_frequency_plot(mutations, output_file=None, title="Mutation Frequency vs. Chromosome Location", 
                         figsize=(12, 8), dpi=300, show_plot=False):
    """
    Create a plot showing mutation frequency vs. chromosome location.
    
    Args:
        mutations (dict): Dictionary with chromosome as key and list of (position, frequency) tuples as value
        output_file (str): Optional output file path for saving the plot
        title (str): Plot title
        figsize (tuple): Figure size (width, height)
        dpi (int): DPI for saved plots
        show_plot (bool): Whether to display the plot
        
    Returns:
        matplotlib.figure.Figure: The created figure object
    """
    if not mutations:
        logger.warning("No mutations to plot")
        return None
    
    # Set up the plot
    num_chroms = len(mutations)
    fig, axes = plt.subplots(
        num_chroms,
        1,
        figsize=(figsize[0], figsize[1] * num_chroms),
        constrained_layout=True,
    )
    if num_chroms == 1:
        axes = [axes]
    
    # Color palette for chromosomes
    colors = plt.cm.Set3(np.linspace(0, 1, num_chroms))
    
    for i, (chrom, chrom_mutations) in enumerate(mutations.items()):
        if not chrom_mutations:
            logger.warning(f"No mutations found for chromosome {chrom}")
            continue
            
        # Sort by position
        chrom_mutations.sort(key=lambda x: x[0])
        positions, frequencies = zip(*chrom_mutations)
        
        # Create scatter plot
        axes[i].scatter(positions, frequencies, alpha=0.6, s=20, color=colors[i])
        
        # Add trend line if there are multiple points
        if len(positions) > 1:
            try:
                z = np.polyfit(positions, frequencies, 1)
                p = np.poly1d(z)
                axes[i].plot(positions, p(positions), "r--", alpha=0.8, linewidth=1)
            except np.RankWarning:
                logger.debug(f"Could not fit trend line for chromosome {chrom}")
        
        # Customize axes
        axes[i].set_xlabel('Position on Chromosome')
        axes[i].set_ylabel('Mutation Frequency (%)')
        axes[i].set_title(f'Chromosome {chrom}')
        axes[i].grid(True, alpha=0.3)
        
        # Format x-axis to show positions in millions
        if max(positions) > 1000000:
            axes[i].xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1000000:.1f}M'))
        
        # Set y-axis limits
        axes[i].set_ylim(0, 100)
        
        # Add statistics
        mean_freq = np.mean(frequencies)
        max_freq = np.max(frequencies)
        axes[i].text(0.02, 0.98, f'Mean: {mean_freq:.1f}%\nMax: {max_freq:.1f}%\nCount: {len(positions)}', 
                    transform=axes[i].transAxes, verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    fig.suptitle(title, fontsize=16)
    
    if output_file:
        try:
            plt.savefig(output_file, dpi=dpi, bbox_inches='tight')
            logger.info(f"Plot saved to {output_file}")
        except Exception as e:
            logger.error(f"Error saving plot: {e}")
    
    if show_plot:
        plt.show()
    
    return fig

def plot_vcf_frequency(vcf_file, output_file=None, title=None, show_plot=False, control_sample: Optional[str] = None, min_dp: int = 0, **kwargs):
    """
    Convenience function to parse VCF and create frequency plot.
    
    Args:
        vcf_file (str): Path to VCF file
        output_file (str): Optional output file path
        title (str): Optional plot title
        **kwargs: Additional arguments passed to create_frequency_plot
        
    Returns:
        matplotlib.figure.Figure: The created figure object
    """
    if title is None:
        vcf_path = Path(vcf_file)
        title = f"Mutation Frequency vs. Chromosome Location - {vcf_path.parent.name}"
    
    logger.info(f"Parsing VCF file: {vcf_file}")
    mutations = parse_vcf_frequency(vcf_file, control_sample=control_sample, min_dp=min_dp)
    
    if not mutations:
        logger.warning("No mutations found in VCF file")
        return None
    
    logger.info(f"Found mutations on {len(mutations)} chromosomes:")
    for chrom, chrom_mutations in mutations.items():
        logger.info(f"  Chromosome {chrom}: {len(chrom_mutations)} mutations")
    
    return create_frequency_plot(mutations, output_file, title, **kwargs)

def get_mutation_statistics(mutations):
    """
    Calculate summary statistics for mutations.
    
    Args:
        mutations (dict): Dictionary with chromosome as key and list of (position, frequency) tuples as value
        
    Returns:
        dict: Dictionary with summary statistics
    """
    stats = {}
    
    for chrom, chrom_mutations in mutations.items():
        if not chrom_mutations:
            continue
            
        positions, frequencies = zip(*chrom_mutations)
        
        stats[chrom] = {
            'count': len(positions),
            'mean_frequency': np.mean(frequencies),
            'median_frequency': np.median(frequencies),
            'max_frequency': np.max(frequencies),
            'min_frequency': np.min(frequencies),
            'std_frequency': np.std(frequencies),
            'min_position': min(positions),
            'max_position': max(positions)
        }
    
    return stats

def main():
    """
    Command-line interface for the plotting module.
    This allows the module to be used as a standalone script.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Plot mutation frequency vs. chromosome location from VCF file')
    parser.add_argument('vcf_file', help='Input VCF file path')
    parser.add_argument('-o', '--output', help='Output plot file path (optional)')
    parser.add_argument('-t', '--title', help='Plot title (optional)')
    parser.add_argument('--no-show', action='store_true', help='Do not display the plot (useful for headless environments)')
    parser.add_argument('--control', help='Name of control sample (to exclude from frequency calculation)')
    parser.add_argument('--min-dp', type=int, default=0, help='Minimum total depth required to include a site (default: 0)')
    parser.add_argument('--dpi', type=int, default=300, help='DPI for saved plots (default: 300)')
    parser.add_argument('--figsize', nargs=2, type=float, default=[12, 8], 
                       help='Figure size as width height (default: 12 8)')
    
    args = parser.parse_args()
    
    try:
        # Set up logging
        logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
        
        # Create the plot
        fig = plot_vcf_frequency(
            args.vcf_file, 
            output_file=args.output, 
            title=args.title,
            show_plot=not args.no_show,
            control_sample=args.control,
            min_dp=args.min_dp,
            dpi=args.dpi,
            figsize=tuple(args.figsize)
        )
        
        if fig is None:
            sys.exit(1)
            
        # Print statistics
        mutations = parse_vcf_frequency(args.vcf_file)
        stats = get_mutation_statistics(mutations)
        
        print("\n📊 MUTATION STATISTICS:")
        print("=" * 50)
        for chrom, chrom_stats in stats.items():
            print(f"\nChromosome {chrom}:")
            print(f"  Count: {chrom_stats['count']}")
            print(f"  Mean frequency: {chrom_stats['mean_frequency']:.2f}%")
            print(f"  Max frequency: {chrom_stats['max_frequency']:.2f}%")
            print(f"  Position range: {chrom_stats['min_position']:,} - {chrom_stats['max_position']:,}")
        
        if args.output:
            print(f"\n✅ Plot saved to: {args.output}")
            
    except FileNotFoundError:
        print(f"❌ Error: VCF file '{args.vcf_file}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
