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
    - AD[snp_index]/DP > 30%
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
            ALT = m[4].split(',')
            if REF == "G" and "A" in ALT:
                snp_index = ALT.index("A")
            elif REF == "C" and "T" in ALT:
                snp_index = ALT.index("T")
            else:
                continue
            INFO = m[7]
            FORMAT_DEF = m[8].split(":")
            AD_index = FORMAT_DEF.index("AD") # here you gotta find the allele you want
            DP_index = FORMAT_DEF.index("DP")
            SAMPLE_INFO = m[-1]
            AD = int(SAMPLE_INFO.split(":")[AD_index].split(',')[snp_index+1])
            DP = int(SAMPLE_INFO.split(":")[DP_index])
            if AD/DP >= 0.3:
                vcf_filt.write(l)
    vcf_filt.close()
