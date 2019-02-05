#!env/bin/python

import sys
import threading
import time
import string
import json
import random
import subprocess
import math
import base64
from datetime import datetime
import os

from stem.control import Controller
from stem import SocketError, UnsatisfiableRequest
import stem.process
from flask import Flask, send_file

from common import tile_deg2num

WEB_SOCKET = 'srv.sock'
SOCKS_SOCKET = 'tor-socks.sock'
CONTROL_SOCKET = 'tor-control.sock'

app = Flask(__name__)

if 0:
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

path = ''.join(random.sample(string.ascii_letters, 1)[0]
        for _ in range(10))

def get_data_uri(mime, data):
    data64 = u''.join(base64.encodebytes(data).decode('ascii').splitlines())
    return u'data:%s;base64,%s' % (mime, data64)

import io
from PIL import Image, ImageDraw
def image_with_location(fn, xfrac, yfrac):
    im = Image.open(fn)
    im = im.convert('RGB')
    draw = ImageDraw.Draw(im)
    cx = int(im.width*xfrac)
    cy = int(im.height*yfrac)
    r = 5
    draw.ellipse([(cx-r, cy-r), (cx+r, cy+r)], fill=(80,80,255))
    draw.ellipse([(cx-r, cy-r), (cx+r, cy+r)], outline=(20,20,20))
    del draw
    bio = io.BytesIO()
    im = im.convert('P', dither=Image.NONE)
    im.save(bio, 'PNG')
    return bio.getvalue()

@app.route('/'+path)
def index():
    show_notification('viewed at %s' % datetime.now().strftime('%H:%M'))

    def page(content):
        return r'''
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
            img {
                margin: 10px;
            }
            </style>
        </head>
        <body>
            <pre>time: %s</pre>
            %s
        </body></html>
        ''' % (datetime.now().strftime('%Y-%m-%d %H:%M'), content)
    d = gps_tracker.location
    if d == None:
        return page(r'''
            <pre>location is not available yet. please wait.</pre>
            ''')
    else:
        lat, lon = d['latitude'], d['longitude']
        imgs = ''
        for z in [15, 12, 9, 6]:
            x, y = tile_deg2num(lat, lon, z)
            xfrac = x - int(x); x = int(x)
            yfrac = y - int(y); y = int(y)
            fn = 'maps/tiles/%d/%d-%d.png' % (z, x, y)
            # imgdata = open(fn, 'rb').read()
            imgdata = image_with_location(fn, xfrac, yfrac)
            imgs += '<img src="%s"><br/>\n' % get_data_uri('image/png', imgdata)
        return page(r'''
            <pre>lat: %(lat).6f, lon: %(lon).6f</pre>
            %(imgs)s
            ''' % locals())

# @app.route('/'+path+'/tiles/<z>/<t>')
# def tile(z, t):
#     z = int(z)
#     x, y = map(int, t.split('.')[0].split('-'))
#     print((z, x, y))
#     fn = 'maps/tiles/%d/%d-%d.png' % (z, x, y)
#     return send_file(fn, mimetype='image/png')

def start_web_app():
    print('Starting web app...')
    if os.path.exists(WEB_SOCKET):
        os.remove(WEB_SOCKET)
    import socket
    from werkzeug.serving import make_server, WSGIRequestHandler
    WSGIRequestHandler.address_string = lambda self: '?'
    WSGIRequestHandler.port_integer = lambda self: 777
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(WEB_SOCKET)
    fd = sock.fileno()
    sock.listen(1)
    srv = make_server(host='', port=None, app=app, threaded=True, fd=fd)
    srv.serve_forever()

def gps_tracker():
    while True:
        try:
            gps_tracker.location = json.loads(subprocess.check_output('termux-location', shell=True))
        except Exception as e:
            print(e)
            time.sleep(2)
        else:
            time.sleep(15)
gps_tracker.location = None

def start_thread(func):
    t = threading.Thread(target=func)
    t.daemon = True
    t.start()
    return t

def show_notification(content):
    subprocess.check_output('termux-notification --id tor-share-location --title tor-share-location', input=content.encode('utf8'), shell=True)

def start_tor_process():
    print('Starting Tor...')

    lines = []
    def print_bootstrap_lines(line):
        lines.append(line)
        if 'Bootstrapped ' in line:
            print(line)

    try:
        proc = stem.process.launch_tor_with_config(
          config = {
            'DataDirectory': 'data',
            'SocksPort': 'unix://%s/%s' % (os.getcwd(), SOCKS_SOCKET),
            'ControlPort': 'unix://%s/%s' % (os.getcwd(), CONTROL_SOCKET),
            # 'ExitNodes': '{ru}',
          },
          init_msg_handler = print_bootstrap_lines,
        )
        print('Tor process id:', proc.pid)
        with open('data/pid', 'w+') as f: f.write('%d\n' % proc.pid)
        return proc
    except:
        print('\n'.join(lines))
        raise

def main():
    if 1: tor_process = start_tor_process()
    else: tor_process = None

    start_thread(start_web_app)
    start_thread(gps_tracker)

    try:
        c = Controller.from_socket_file(CONTROL_SOCKET)
        c.authenticate()
    except SocketError:
        print('Cannot connect to Tor control port.')
        sys.exit()

    try:
        print('Creating hidden service...')
        res = c.create_ephemeral_hidden_service({
            80: 'unix:'+WEB_SOCKET,
        }, await_publication=True)
        assert res.is_ok()
        svcid = res.service_id
        link = 'http://%s.onion/%s' % (svcid, path)
        print(' * Created service:', link)
    except Exception as e:
        print(e)
        sys.exit(1)

    print('Waiting for location...')
    while not gps_tracker.location:
        time.sleep(1)
    print(' * location ready')

    if input('Share onion link? [Y/n] ').lower() in ['', 'y']:
        subprocess.check_output('termux-share -a send', shell=True, input=link.encode())

    input('Press enter to quit sharing location> ')

    c.remove_ephemeral_hidden_service(svcid)

    c.close()

    if tor_process:
        tor_process.terminate()
        tor_process.wait()
        #os.remove('data/lock')

    print('Finished.')

if __name__ == '__main__':
    if 1:
        main()
    if 0:
        start_thread(gps_tracker)
        start_web_app()

