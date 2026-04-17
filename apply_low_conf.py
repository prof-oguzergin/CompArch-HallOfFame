"""Manually apply the verified low-confidence corrections."""
import re, sys
sys.stdout.reconfigure(encoding='utf-8')

# (our_conf_prefix, our_title_prefix, new_conf, new_title)
# Verified as same paper despite low title-match score
corrections = [
    ('ISCA 2024', 'Assessing processor sustainability', 'ASPLOS 2024', 'FOCAL: A First-Order Carbon Model to Assess Processor Sustainability'),
    ('ASPLOS 2024', 'Enabling sustainable cloud computing', 'ISCA 2024', 'Designing Cloud Servers for Lower Carbon'),
    ('ISCA 2005', 'Tolerating Cache-Miss Latency with Multipass', 'MICRO 2005', '"Flea-flicker" Multipass Pipelining: An Alternative to the High-Power Out-of-Order Offense'),
    ('ISCA 2006', '3D Integration for Introspection', 'ASPLOS 2006', 'Introspective 3D chips'),
    ('ISCA 2006', 'A Top-Down Approach to Architecting CPI', 'ASPLOS 2006', 'A performance counter architecture for computing accurate CPI components'),
    ('MICRO 2007', 'Toward Ideal On-Chip Communication Using Express', 'ISCA 2007', 'Express virtual channels: towards the ideal interconnection fabric'),
    ('ASPLOS 2009', 'Predicting Voltage Droops Using Recurring', 'HPCA 2009', 'Voltage emergency prediction: Using signatures to reduce operating margins'),
    ('MICRO 2014', 'A High-Throughput Neural Network Accelerator', 'ASPLOS 2014', 'DianNao: a small-footprint high-throughput accelerator for ubiquitous machine-learning'),
    ('ISCA 2014', 'Address Translation for Throughput-Oriented', 'ASPLOS 2014', 'Architectural support for address translation on GPUs: designing memory management units for CPU/GPUs with unified address spaces'),
    ('ISCA 2015', 'Nonvolatile Processor Architectures: Efficient, Reliable Progress', 'HPCA 2015', 'Architecture exploration for ambient energy harvesting nonvolatile processors'),
    ('ISCA 2016', 'The Memristive Boltzmann Machines', 'HPCA 2016', 'Memristive Boltzmann machine: A hardware accelerator for combinatorial optimization and deep learning'),
    ('ISCA 2016', 'Configurable Clouds', 'MICRO 2016', 'A cloud-scale acceleration architecture'),
    ('ISCA 2019', 'Trace Wringing for Program Trace Privacy', 'ASPLOS 2019', 'Safer Program Behavior Sharing Through Trace Wringing'),
    ('USENIX Security 2023', 'Hardware-assisted fault isolation: Going beyond', 'ASPLOS 2023', 'Going beyond the Limits of SFI: Flexible and Secure Hardware-Assisted In-Process Isolation with HFI'),
    ('ASPLOS 2023', 'Distributed brain-computer interfacing with', 'ISCA 2023', 'SCALO: An Accelerator-Rich Distributed System for Scalable Brain-Computer Interfacing'),
]
# 2 NOT applied (likely false matches):
# - ISCA 2003 "Transactional Execution: Toward Reliable..." (different paper than Checkpoint Processing)
# - ISCA 2011 "Supporting Very Large DRAM Caches..." (different paper than PCM bank)

with open('data.js','r',encoding='utf-8') as f:
    content = f.read()

def js_esc(s):
    return s.replace('\\','\\\\').replace('"','\\"')

applied = 0
for our_conf, our_title_pfx, new_conf, new_title in corrections:
    # Build regex to find the entry
    conf_esc = re.escape(our_conf)
    pfx_esc = re.escape(our_title_pfx)
    # Match: conf:"our_conf",title:"our_title_starts_with_pfx"
    p = re.compile(rf'conf:"{conf_esc}",title:"{pfx_esc}[^"]*"')
    m = p.search(content)
    if not m:
        print(f'! NOT FOUND: {our_conf} / {our_title_pfx}', file=sys.stderr)
        continue
    new_str = f'conf:"{new_conf}",title:"{js_esc(new_title)}"'
    content = content[:m.start()] + new_str + content[m.end():]
    applied += 1
    print(f'  ✓ {our_conf} -> {new_conf}: {new_title[:60]}')

with open('data.js','w',encoding='utf-8') as f:
    f.write(content)

print(f'\nApplied {applied}/{len(corrections)} corrections')
