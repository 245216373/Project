#!/bin/bash

cd "$(dirname $(readlink -f $0))"/..

docker stop live_gateway-d; docker rm -f live_gateway-d
