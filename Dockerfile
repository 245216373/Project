FROM registry.cn-shenzhen.aliyuncs.com/aymazon/bi-py:1.0.0

CMD ["/sbin/my_init"]

COPY requirements.txt /tmp/

RUN export DEBIAN_FRONTEND=noninteractive \
    && apt update \
    && apt-get install -y -q \
    gcc python-dev zlib1g-dev \
    && source /python-env/bin/activate \
    && sed -i '/^cx_Freeze.*/d' /tmp/requirements.txt \
    && pip install -i https://pypi.douban.com/simple -r /tmp/requirements.txt && rm /tmp/requirements.txt \
    && apt-get autoremove -y gcc python-dev zlib1g-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY bin/u14/opt /opt/

RUN true \
    && echo -e "\n/opt/nginx\n/opt/ffmpeg" >> /etc/ld.so.conf && ldconfig \
    && mv /opt/nginx/nginx /usr/bin/ && mv /opt/ffmpeg/ffmpeg /usr/bin && mv /opt/ffmpeg/ffprobe /usr/bin \
    && mkdir -p /mnt/nas \
    && mkdir -p /var/opt/nginx/record && mkdir -p /var/opt/nginx/vod && mkdir -p /var/opt/nginx/upload && mkdir -p /mnt/nas \
    && mkdir /etc/service/nginx && touch /etc/service/nginx/run && chmod +x /etc/service/nginx/run \
    && echo -e "#!/bin/bash\nmkdir -p /usr/local/live-gateway/logs\nenvsubst < /opt/nginx/nginx.conf.template > /opt/nginx/nginx.conf\nnginx -c /opt/nginx/nginx.conf" > /etc/service/nginx/run \
    && mkdir /etc/service/app && touch /etc/service/app/run && chmod +x /etc/service/app/run \
    && echo -e "#!/bin/bash\nsource /python-env/bin/activate\ncd /app\npython main.py" > /etc/service/app/run \
    && echo -e "#!/bin/bash\nsource /python-env/bin/activate\ncd /app\nrm -rf /etc/service/app\nkill -9 \$(ps -ef | grep main.py | grep -v grep | awk '{print \$2}')\nexec bash" > /debug_app.sh && chmod +x /debug_app.sh \
    && echo -e "#!/bin/bash\nsource /python-env/bin/activate\ncd /app\nexec bash" > /test_app.sh && chmod +x /test_app.sh \
    && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY src /app
