"""Dig the concrete releases: bowlroll voicebank download, open datasets, model links."""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import urllib.error

sys.stdout.reconfigure(encoding='utf-8')
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'
OUT = r'D:\code\DSH_PlainRiceWhale\tools\voice_release'
os.makedirs(OUT, exist_ok=True)


def get(url, headers=None, tries=2, wait=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=headers or {'User-Agent': UA, 'Accept': '*/*'})
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.status, r.read().decode('utf-8', 'ignore')
        except urllib.error.HTTPError as e:
            if e.code in (403, 429):
                time.sleep(wait * (i + 2))
                continue
            return e.code, ''
        except Exception:
            time.sleep(wait)
    return None, ''


BVS = {
    'BV1n3Hf6xERq': '大肥鱼少女音 数据集已开源',
    'BV1c7eE6VEMD': '给大肥鱼捏了少女感音色',
    'BV1EJg36xE23': '攻略大肥鱼声线后续',
    'BV18KgK6fEyK': '攻略肥鱼声线发现大大问题',
    'BV1ajHT6cEgX': '大肥鱼接入一切音频软件',
    'BV1DiHK6tE8Y': '基于大肥鱼的套皮龙娘GPT桌宠',
    'BV16rnH6jEPJ': '透音アリク提醒调声（dsh大肥鱼插件）',
}
for bv, note in BVS.items():
    url = f'https://api.bilibili.com/x/web-interface/view?bvid={bv}'
    st, b = get(url, headers={'User-Agent': UA, 'Referer': 'https://www.bilibili.com/'})
    try:
        d = json.loads(b)['data']
        print('===', bv, '|', note)
        print('   title:', d.get('title'))
        print('   UP:', (d.get('owner') or {}).get('name'))
        print('   DESC:', str(d.get('desc') or '').replace('\n', ' | ')[:1500])
        # links inside desc
        for l in re.findall(r'https?://[^\s，。）)]+', str(d.get('desc') or '')):
            print('   LINK:', l)
    except Exception as e:
        print('===', bv, 'fail', st, e, (b or '')[:100])
    time.sleep(4)

print()
print('=== bowlroll download route ===')
st, b = get('https://bowlroll.net/file/360563')
if b:
    for m in re.findall(r'(?:href|action)="([^"]+)"', b):
        if any(k in m.lower() for k in ('dl', 'download', 'file/360563')):
            print('  ', m[:160])
    for m in re.findall(r'(?:data-[\w-]+|onclick)="([^"]*360563[^"]*)"', b):
        print('  onclick:', m[:160])
