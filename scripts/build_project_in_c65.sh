#!/bin/bash

cd "$(dirname $(readlink -f $0))"/..

PATH=$PATH:$HOME/bin

export PATH
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
if command -v pyenv 1>/dev/null 2>&1; then
  eval "$(pyenv init -)"
fi
export PYTHON_CONFIGURE_OPTS="--enable-shared"
export PYTHONASYNCIODEBUG=1

eval "$(pyenv virtualenv-init -)"

pyenv activate live-gateway
rm build -rf && mkdir build

python setup.py build
cd build
rm live-gateway -rf; mv exe.linux-x86_64-* live-gateway && tar zcf live-gateway.tar.gz live-gateway
cd ..

python setup-ice.py build
cd build
rm live-gateway-ice -rf; mv exe.linux-x86_64-* live-gateway-ice && tar zcf live-gateway-ice.tar.gz live-gateway-ice
cd ..
