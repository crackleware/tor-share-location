#!/usr/bin/env sh

set -xe

pkg install -y tor python libjpeg-turbo-dev clang curl

mkdir -p deps
[ -f zlib-1.2.11.tar.gz ] || {
    curl https://www.zlib.net/zlib-1.2.11.tar.gz -o dl.tmp
    mv dl.tmp zlib-1.2.11.tar.gz
}

cd deps
tar xvf zlib-1.2.11.tar.gz
cd zlib-1.2.11
./configure --prefix=`pwd`-inst
make install
cd ../..

#python -m pip install --user virtualenv
#python -m virtualenv env
python -m venv env

CFLAGS="-I`pwd`/deps/zlib-1.2.11-inst/include" env/bin/pip install -r requirements.txt


