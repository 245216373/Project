#!/bin/bash

cd "$(dirname $(readlink -f $0))"/..

ssh root@$1 'rm -rf /opt/cloudroom/distrib/LiveGateway \
    && mkdir -p /opt/cloudroom/logs/LiveGateway && chown crproj: /opt/cloudroom/logs/LiveGateway \
    && mkdir -p /opt/cloudroom/var/LiveGateway/nginx/record && mkdir -p /opt/cloudroom/var/LiveGateway/nginx/vod  && chown -R crproj: /opt/cloudroom/var/LiveGateway \
    && mkdir -p /opt/cloudroom/var/lib/crproj/LiveGateway && chown -R crproj: /opt/cloudroom/var/lib/crproj/LiveGateway \
    && mkdir -p /opt/cloudroom/distrib/LiveGateway && chown -R crproj: /opt/cloudroom/distrib/LiveGateway'

rsync -avz --progress -h bin/c65/opt/ffmpeg root@$1:/opt/cloudroom/distrib/LiveGateway/
rsync -avz --progress -h bin/c65/opt/nginx root@$1:/opt/cloudroom/distrib/LiveGateway/
rsync -avz --progress -h build/live-gateway.tar.gz root@$1:/opt/cloudroom/distrib/LiveGateway/
rsync -avz --progress -h build/live-gateway-ice.tar.gz root@$1:/opt/cloudroom/distrib/LiveGateway/
rsync -avz --progress -h env-zj-template root@$1:/opt/cloudroom/var/lib/crproj/LiveGateway/

ssh root@$1 "cd /opt/cloudroom/distrib/LiveGateway \
    && tar zxf live-gateway.tar.gz && tar zxf live-gateway-ice.tar.gz \
    && rm -rf live-gateway.tar.gz && rm -rf live-gateway-ice.tar.gz \
    && chown -R crproj: /opt/cloudroom/var/lib/crproj/LiveGateway/ \
    && chown -R crproj: /opt/cloudroom/distrib/LiveGateway \
    ; ps -ef | grep '/distrib/LiveGateway/' | grep -v grep | grep -v vim \
    ; kill -TERM \$(ps -ef | grep '/distrib/LiveGateway/' | grep -v grep | grep -v vim | awk '{print \$2}') \
    ; echo 'sleep 5' && sleep 5 \
    ; ps -ef | grep '/distrib/LiveGateway/' | grep -v grep | grep -v vim \
    "

