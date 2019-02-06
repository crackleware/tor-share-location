#!/usr/bin/env sh

set -xe

pkg install -y tor python libjpeg-turbo-dev clang curl

mkdir -p deps
cd deps
[ -f zlib-1.2.11.tar.gz ] || {
    curl https://www.zlib.net/zlib-1.2.11.tar.gz -o dl.tmp
    mv dl.tmp zlib-1.2.11.tar.gz
    sha256sum -c <<EOF
c3e5e9fdd5004dcb542feda5ee4f0ff0744628baf8ed2dd5d66f8ca1197cb1a1  zlib-1.2.11.tar.gz
EOF
}
tar xvf zlib-1.2.11.tar.gz
cd zlib-1.2.11
./configure --prefix=`pwd`-inst
make install
cd ../..

#python -m pip install --user virtualenv
#python -m virtualenv env
python -m venv env

CFLAGS="-I`pwd`/deps/zlib-1.2.11-inst/include" env/bin/pip install --no-binary all --require-hashes -r requirements.txt

echo Dependencies successfully installed.

