#!/bin/bash

cd "$(dirname $(readlink -f $0))"/..

docker build -f Dockerfile --compress -t live_gateway:d . && docker stop live_gateway-d; docker run --rm -t --env-file=$(pwd)/.env --name live_gateway-d -p 8511:1935 -p 8512:80 -p 8513:8081 -v $(pwd)/tests:/app/tests -d --cap-add=SYS_PTRACE live_gateway:d /sbin/my_init && docker logs --details -f live_gateway-d
