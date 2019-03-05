#!/bin/bash

cd "$(dirname $(readlink -f $0))"/..

rsync -avzu --delete --progress -h --exclude-from=.gitignore ./ crproj@10.8.8.237:~/code/live-gateway/
ssh crproj@10.8.8.237 "~/code/live-gateway/scripts/build_project_in_c65.sh"
rsync -avz --progress -h --remove-source-files crproj@10.8.8.237:~/code/live-gateway/build/live-gateway.tar.gz build/live-gateway.tar.gz
rsync -avz --progress -h --remove-source-files crproj@10.8.8.237:~/code/live-gateway/build/live-gateway-ice.tar.gz build/live-gateway-ice.tar.gz
