#!/bin/bash

cd "$(dirname $(readlink -f $0))"/..
cd docs; rm _build -rf; make html > /dev/null 2>&1; cd ..; xdg-open docs/_build/html/index.html > /dev/null 2>&1
