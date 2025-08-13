import os, sys

def check_tmp_dir(dir):
    if os.getenv("TMP"):
        TMP = os.getenv("TMP")
    else:
        TMP = dir
    return TMP

def get_datasets_for_symlinks(df, sample = None, library = None, d = None, infolder="data/reads", outfolder="data/reads"):
    dataset_file = None
    for row in df.itertuples():
        if library is None:
            if getattr(row, "sample") == sample:
                dataset_file = os.path.join(outfolder, getattr(row, d))
        else:
            if getattr(row, "sample") == sample and getattr(row, "library") == library:
                dataset_file = os.path.join(outfolder, getattr(row, d))
    return dataset_file

def get_control_samples(df):
    """
    output is CTRL as a string, and SAMPLES as a list
    Supports 1 control and multiple mutants
    """
    ctrl = set()
    samples = set()
    for row in df.itertuples():
        if getattr(row, "sample_type") == "control":
            ctrl.add(getattr(row, "sample"))
        if getattr(row, "sample_type") == "mutated":
            samples.add(getattr(row, "sample"))
    if len(ctrl) < 1:
        sys.exit("No control specified in the datasets.tab file!")
    elif len(ctrl) > 1:
        sys.exit(">1 controls specified in the datasets.tab file!")
    if len(samples) < 1:
        sys.exit("No mutant samples specified in the datasets.tab file!")
    return list(ctrl)[0], list(samples)

def fastqc_raw_outputs(datasets_tab = None, analysis_tab = None, infolder="data/reads", outfolder="results/fastqc_raw", ext=".fastq.gz"):
    fastqc_out = []
    for i,l in datasets_tab.iterrows():
        #if l["sample"] in list(analysis_tab["sample"]):
        fastqc_out.append(os.path.join(outfolder, "{sample_ctrl}_{library}.R1_fastqc.html".format(sample_ctrl = l["sample"], library = l["library"])))
        fastqc_out.append(os.path.join(outfolder, "{sample_ctrl}_{library}.R2_fastqc.html".format(sample_ctrl = l["sample"], library = l["library"])))
    return fastqc_out

def get_sample_bamfiles(df, res_dir="results", sample = None, library = None, ref_genome_mt = None, ref_genome_n = None):
    outpaths = []
    for row in df.itertuples():
        if getattr(row, "sample") == sample:
            #bam_file =
            bam_file = "{sample}_{library}_OUT-sorted.bam".format(sample = sample, library = getattr(row, "library"), ref_genome_mt = ref_genome_mt, ref_genome_n = ref_genome_n)
            out_folder = "OUT_{base}".format(base = bam_file.replace("_OUT-sorted.bam", ""))
            outpaths.append("{results}/{sample}/map/{out_folder}/{bam_file}".format(results = res_dir, bam_file = bam_file, sample = sample, out_folder = out_folder))
    return outpaths  
