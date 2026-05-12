import sys
p = 'setup/setup_environment.py'
txt = open(p, encoding='utf-8').read()
txt = txt.replace('f"  {G}\u2713{RST}', 'f"  {G}[OK]{RST}')
txt = txt.replace('f"  {R}\u2717{RST}', 'f"  {R}[!!]{RST}')
txt = txt.replace('f"  {Y}\u26a0{RST}', 'f"  {Y}[WW]{RST}')
txt = txt.replace('f"  {B}\u00b7{RST}', 'f"  {B}[..]{RST}')
txt = txt.replace('installed \u2713', 'installed OK')
txt = txt.replace('{G}\u2713{RST}', '{G}[OK]{RST}')
txt = txt.replace('{R}\u2717{RST}', '{R}[!!]{RST}')
txt = txt.replace('\u2500'*50, '-'*50)
txt = txt.replace('\u2714'*60, '='*60)
open(p, 'w', encoding='utf-8').write(txt)
print('Patched OK')
