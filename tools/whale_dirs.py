"""Inspect whale-audio / whale-roles (hidden files too) and any voice-model traces."""
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
h = os.path.expanduser('~/.dsh')
for d in ('whale-audio', 'whale-roles'):
    p = os.path.join(h, d)
    print('===', p, 'exists=', os.path.exists(p))
    for root, dirs, files in os.walk(p):
        print('  DIR', root, '| subdirs', dirs, '| files', files[:20], '| count', len(files))
        for f in files[:20]:
            fp = os.path.join(root, f)
            try:
                print('     ', f, os.path.getsize(fp))
            except Exception as e:
                print('     ', f, 'err', e)
