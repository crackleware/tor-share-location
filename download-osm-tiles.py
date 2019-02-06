#!env/bin/python

import sys
import os
import requests
import time
import json
import subprocess

from common import tile_deg2num

outdir = 'maps/tiles'

print('Select location:')
print('1) by termux-location command (current location)')
print('2) by city name')
print('3) by latitude and longitude')
r = input('> ').strip()
if   r == '1':
    d = json.loads(subprocess.check_output('termux-location', shell=True))
    lat, lon = d['latitude'], d['longitude']
    print('latitude and longitude: %s, %s' % (lat, lon))
elif r == '2':
    cities = [s.split('\t') for s in open('cities.tsv').read().split('\n') if s][1:]
    cities = sorted(cities, key=lambda c: c[0])
    for i, r in enumerate(cities):
        name_en, name, country = r[0:3]
        print('%d) %s (%s), %s' % (i+1, name_en, name, country))
    name_en, name, country, lat, lon = cities[int(input('> '))-1]
    lat, lon = float(lat), float(lon)
    print('%s (%s), %s - latitude and longitude: %s, %s' % (name_en, name, country, lat, lon))
elif r == '3':
    r = input('Latitude and longitude (ex: 12.345, 56.234): ')
    lat, lon = [float(s) for s in r.replace(',', ' ').split()
                if s]
else:
    print('exiting.')
    sys.exit(1)

zmax = 15
x, y = tile_deg2num(lat, lon, zmax)
x, y = int(x), int(y)

# TODO: better radius selection
r = input('Radius tiles? (50) ')
if r: r = int(r)
else: r = 50

xrng = (x-r//2, x+r//2)
yrng = (y-r//2, y+r//2)

def tiles_iter():
    for z in [6, 9, 12, 15]:
        k = 2**(zmax-z)
        xmin, xmax = xrng[0]//k, xrng[1]//k
        ymin, ymax = yrng[0]//k, yrng[1]//k
        for x in range(xmin, xmax+1):
            for y in range(ymin, ymax+1):
                yield z, x, y

cnt = len(list(tiles_iter()))
for i, (z, x, y) in enumerate(tiles_iter()):
    od = outdir+'/%d' % z
    os.makedirs(od, exist_ok=True)
    fn = od+'/%d-%d.png' % (x, y)
    if not os.path.exists(fn):
        print('downloading (%d/%d)' % (i+1, cnt), fn)
        try:
            d = requests.get('https://a.tile.openstreetmap.org/%d/%d/%d.png' % (z, x, y))
            with open(fn+'.tmp', 'wb+') as f: f.write(d.content)
            os.rename(fn+'.tmp', fn)
        except Exception as e:
            print(e)
        time.sleep(1)

print('Finished.')

