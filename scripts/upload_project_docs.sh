#!/bin/bash

cd "$(dirname $(readlink -f $0))"/..

rsync -avzu --delete --progress -h docs/_build/html/ root@10.8.8.207:/docker/nginx-server/html/docs/live-gateway/

