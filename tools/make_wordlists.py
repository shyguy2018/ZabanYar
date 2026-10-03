"""Regenerates data/en.txt and data/fa.txt (word<TAB>zipf frequency).
   Run automatically by build.bat, run.bat and GitHub Actions."""
import re
import os
import wordfreq

os.makedirs("data", exist_ok=True)

en = [w for w in wordfreq.top_n_list('en', 70000) if re.fullmatch(r"[a-z]+('[a-z]+)?", w)]
fa = [w for w in wordfreq.top_n_list('fa', 90000) if re.fullmatch('[\u0600-\u06FF\u200c]+', w)]
with open('data/en.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(f'{w}\t{wordfreq.zipf_frequency(w, "en"):.2f}' for w in en))
with open('data/fa.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(f'{w}\t{wordfreq.zipf_frequency(w, "fa"):.2f}' for w in fa))
print(len(en), len(fa))
