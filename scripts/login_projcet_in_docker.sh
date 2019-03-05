#!/bin/bash

cd "$(dirname $(readlink -f $0))"/..

docker exec -it live_gateway-d bash
