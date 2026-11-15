"""Audit every shipped asset for embedded metadata, so PROVENANCE.md can state facts.

Checks PNG text chunks + EXIF, JPEG EXIF/APPn, MP3 ID3/legacy tags, and SVG comments and
identifying attributes. Reports what is actually in the bytes, not what the pipeline
"should" have produced.
"""
import os
import re
import sys

from PIL import Image
from PIL.PngImagePlugin import PngInfo

sys.stdout.reconfigure(encoding='utf-8')
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCAN = [os.path.join(BASE, 'whale-aside'), os.path.join(BASE, 'samples')]

targets = []
for root in SCAN:
    for dirpath, _dirs, files in os.walk(root):
        for name in sorted(files):
            ext = name.lower().rsplit('.', 1)[-1]
            if ext in ('png', 'jpg', 'jpeg', 'gif', 'mp3', 'svg'):
                targets.append(os.path.join(dirpath, name))

print(f'{len(targets)} asset files under whale-aside/\n')
for path in targets:
    rel = os.path.relpath(path, BASE).replace('\\', '/')
    size = os.path.getsize(path)
    kind = 'unknown'
    findings = []
    if path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
        im = Image.open(path)
        kind = im.format
        info_keys = sorted(k for k in im.info if k not in ('duration', 'loop', 'transparency', 'version', 'bitrate'))
        if info_keys:
            findings.append(f'info keys: {info_keys}')
        text = getattr(im, 'text', None)
        if isinstance(text, dict) and text:
            findings.append(f'PNG tEXt: {sorted(text.keys())}')
        exif = im.getexif() if hasattr(im, 'getexif') else {}
        if exif:
            findings.append(f'EXIF tags: {sorted(exif.keys())}')
        # raw scan for the usual markers
        raw = open(path, 'rb').read()
        for marker, label in ((b'Exif', 'APP1/Exif block'), (b'ICC_PROFILE', 'ICC profile'),
                              (b'sWID', 'XMP (old JPEG)')):
            if marker in raw:
                findings.append(f'bytes contain {label}')
        if path.lower().endswith('.png') and b'iTXt' in raw:
            findings.append('PNG iTXt chunk present')
    elif path.lower().endswith('.mp3'):
        raw = open(path, 'rb').read()
        kind = 'MP3'
        if raw[:3] == b'ID3':
            findings.append(f'ID3v2 header, {raw[6]}.{raw[7]}')
            for tag in (b'TIT2', b'TPE1', b'TALB', b'COMM', b'TENC', b'ARTS'):
                if tag in raw[:4096]:
                    findings.append(f'ID3 frame {tag.decode()}')
        else:
            findings.append('no ID3v2 header')
        if b'Xing' in raw[:2048] or b'Info' in raw[:2048]:
            findings.append('LAME/Xing header')
        if b'LAME' in raw:
            findings.append('encoder tag "LAME"')
    elif path.lower().endswith('.svg'):
        kind = 'SVG'
        text = open(path, 'r', encoding='utf-8', errors='replace').read()
        comments = re.findall(r'<!--(.*?)-->', text, re.S)
        if comments:
            findings.append(f'{len(comments)} XML comment(s): {comments[:3]}')
        for attr in ('sodipodi', 'inkscape', 'xmlns:svg', 'dc:', 'cc:', 'rdf:', 'generator', 'id="svg"'):
            if attr in text:
                findings.append(f'contains "{attr}"')
        head = text[:200].replace('\n', ' ')
        findings.append(f'head: {head[:120]}')
    print(f'{rel}  [{kind}, {size/1024:.1f} KB]')
    if findings:
        for f in findings:
            print(f'    - {f}')
    else:
        print('    - (no metadata found)')
