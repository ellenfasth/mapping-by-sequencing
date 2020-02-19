def get_AF(INFO):
    AF = None
    INFO = INFO.split(";")
    print(INFO)
    for field in INFO:
        if field.startswith("AF="):
            try:
                AF = float(field.replace("AF=", ""))
            except:
                pass
            break
    print(AF)
    return AF

def filter_vcf(vcf_file, vcf_filt_file):
    """
    Filter VCF according to:
    - AF > 30%
    - keep only SNPs which has G -> A or C -> T
    
FORMAT/AD   .. Allelic depth (Number=R,Type=Integer)
FORMAT/ADF  .. Allelic depths on the forward strand (Number=R,Type=Integer)
FORMAT/ADR  .. Allelic depths on the reverse strand (Number=R,Type=Integer)
FORMAT/DP   .. Number of high-quality bases (Number=1,Type=Integer)
FORMAT/SP   .. Phred-scaled strand bias P-value (Number=1,Type=Integer)
FORMAT/SCR  .. Number of soft-clipped reads (Number=1,Type=Integer)

INFO/AD     .. Total allelic depth (Number=R,Type=Integer)
INFO/ADF    .. Total allelic depths on the forward strand (Number=R,Type=Integer)
INFO/ADR    .. Total allelic depths on the reverse strand (Number=R,Type=Integer)
INFO/SCR    .. Number of soft-clipped reads (Number=1,Type=Integer)

FORMAT/DV   .. Deprecated in favor of FORMAT/AD; Number of high-quality non-reference bases, (Number=1,Type=Integer)
FORMAT/DP4  .. Deprecated in favor of FORMAT/ADF and FORMAT/ADR; Number of high-quality ref-forward, ref-reverse,
               alt-forward and alt-reverse bases (Number=4,Type=Integer)
FORMAT/DPR  .. Deprecated in favor of FORMAT/AD; Number of high-quality bases for each observed allele (Number=R,Type=Integer)
INFO/DPR    .. Deprecated in favor of INFO/AD; Number of high-quality bases for each observed allele (Number=R,Type=Integer)
    """
    vcf = open(vcf_file, 'r')
    vcf_filt = open(vcf_filt_file, 'w')
    for l in vcf:
        if l.startswith("#"):
            # it's a header
            vcf_filt.write(l)
        else:
            m = l.split()
            REF = m[3]
            ALT = m[4]
            INFO = m[7]
            SAMPLE_INFO = m[-1]
            AF = get_AF(INFO)
            if AF == None:
                continue
            if REF == "G" and ALT == "A" or REF == "C" and ALT == "T":
                if AF >= 0.3:
                    vcf_filt.write(l)
    vcf_filt.close()
