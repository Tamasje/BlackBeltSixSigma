"""Forward-use scan of the study guide: terms used in a part before the part that introduces them.

Usage (from resources/): python3 ../.claude/handoff/forward_scan.py [part ...]
Prints, per unit, the count of terms whose home part is later in the course. The homes are the decision of the
user's ordering request (2026-10-08): every concept is explained where it first appears; later parts only refer back."""
import re, sys, glob, os
HOME = {  # term regex -> home part number
    r'nulhypothese|\bH_?\{?0\}?\b|\\mathrm\{H\}_\{0\}|H_\{0\}|\bH0\b|alternatieve hypothese|HA\b|H_\{A\}': 5,
    r'p-waarde|type I\b|type II|onderscheidingsvermogen|\bkracht\b|significantieniveau|statistisch significant': 5,
    r'OC-curve|OC\(': 6,
    r'\bAQL\b|\bLQL\b|steekproefplan|aanvaardingssteekproef|producentenrisico|consumentenrisico': 6,
    r'kleinste.kwadraten|regressielijn|regressiemodel|\bR\^?\{?2\}?\b adj|residu': 7,
    r'\bANOVA\b|variantieanalyse|proefopzet|\bDOE\b|factorieel|interactie-effect': 8,
    r'\bCpk?\b|C_\{\\mathrm\{p|C_\{p|\bPpk?\b|capabiliteitsindex': 9,
    r'regelkaart|control chart|\bUCL\b|\bLCL\b|\bSPC\b|Western Electric': 10,
    r'\bMSA\b|\bGRR\b|Gage R|herhaalbaarheid|reproduceerbaarheid|meetsysteem': 11,
    r'machine learning|overfitting|underfitting|confusion matrix': 12,
    r'betrouwbaarheidsinterval|\bBI\b|\bCI\b': 4,
    r'sigmaniveau|\bDPMO\b|Z-tabel|standaardnormale': 3,
}
parts = sys.argv[1:] or [f'{i:02d}' for i in range(2, 13)]
for nn in parts:
    f = glob.glob(f'study/parts/{nn}_*.html')[0]
    s = open(f, encoding='utf-8').read()
    for u in re.split(r'(?=<section class="unit" id=")', s)[1:]:
        uid = re.search(r'id="([^"]+)"', u).group(1)
        if uid.endswith('studiewijzer'): continue
        txt = re.sub(r'<div class="exercise".*?</div>\s*</div>', ' ', u, flags=re.S)   # theory only (rough)
        txt = re.sub(r'<a class="p".*?</a>', ' ', txt, flags=re.S)   # page citations such as 'SPC p. 20'
        txt = re.sub(r'<[^>]+>', ' ', txt)
        txt = re.sub(r'\bdeel \d+|Deel \d+|\d\d\.\d+', ' ', txt)
        hits = {}
        for pat, home in HOME.items():
            if home > int(nn):
                n = len(re.findall(pat, txt))
                if n: hits[home] = hits.get(home, 0) + n
        if hits: print(f'{uid:22}', ' '.join(f'deel{h}:{c}' for h, c in sorted(hits.items())))
