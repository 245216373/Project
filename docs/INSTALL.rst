Ubuntu 14.04
============

内网主机： 10.8.8.238
---------------------

编译 ffmpeg
-----------

.. code:: bash

    # 安装依赖
    apt-get update
    apt-get -y install yasm autoconf automake build-essential libtool pkg-config texinfo zlib1g-dev
    apt-get -y install libfdk-aac-dev libx264-dev libmp3lame-dev librtmp-dev

    # 下载 ffmpeg
    wget https://github.com/FFmpeg/FFmpeg/archive/n3.3.8.tar.gz

    # 编译安装 ffmpeg 到 /usr/local/live-gateway/bin
    ./configure --prefix=/usr/local/live-gateway \
    --extra-cflags="-fPIC" \
    --extra-ldflags="-lpthread" \
    --enable-version3 \
    --enable-runtime-cpudetect --disable-iconv \
    --enable-pic --enable-pthreads \
    --disable-shared --enable-static \
    --disable-network --disable-doc \
    --enable-ffmpeg --disable-ffplay --disable-ffserver --enable-ffprobe \
    --enable-gpl --enable-nonfree \
    --enable-libfdk-aac --enable-libmp3lame --enable-librtmp\
    --enable-libx264 --enable-encoder=libx264 --enable-decoder=h264 \
    --disable-debug
    make -j6 && make install

    # 使用 ldd 将依赖库放到与 ffmpeg ffprobe 可执行文件相同的目录下


编译 nginx
----------

.. code:: bash

    # 安装依赖
    apt-get install -y build-essential libpcre3 libpcre3-dev libssl-dev unzip software-properties-common

    # 下载 nginx 和 nginx-rtmp-module
    wget https://github.com/nginx/nginx/archive/release-1.15.2.tar.gz -O nginx-v1.15.2.tar.gz
    wget https://github.com/arut/nginx-rtmp-module/archive/v1.2.1.tar.gz -O nginx-rtmp-module-v1.2.1.tar.gz

    # 编译 nginx 注意 module 版本号
    ./auto/configure --prefix=/usr/local/live-gateway \
    --with-http_ssl_module --with-http_stub_status_module --with-http_secure_link_module \
    --with-http_flv_module --with-http_mp4_module --add-module=../nginx-rtmp-module-1.2.1 --with-debug
    make -j6 && make install

    # 使用 ldd 将依赖库放到与 nginx 可执行文件相同的目录下


编译 live-gateway
-----------------


CentOS 6.5
==========

内网主机： 10.8.8.237
---------------------

编译 ffmpeg
-----------

.. code:: bash

    # 安装依赖
    yum install -y autoconf automake bzip2 cmake freetype-devel gcc gcc-c++ git libtool make mercurial pkgconfig zlib-devel

    # 下载编译 依赖库
    cd /root
    mkdir ~/ffmpeg_sources

    cd ~/ffmpeg_sources
    wget -e use_proxy=yes -e http_proxy=10.8.8.109:502 http://www.nasm.us/pub/nasm/releasebuilds/2.13.02/nasm-2.13.02.tar.bz2
    tar xjvf nasm-2.13.02.tar.bz2
    cd nasm-2.13.02
    ./autogen.sh
    ./configure --prefix="$HOME/ffmpeg_build" --bindir="$HOME/bin"
    make -j6
    make install

    cd ~/ffmpeg_sources
    wget -e use_proxy=yes -e http_proxy=10.8.8.109:502 http://www.tortall.net/projects/yasm/releases/yasm-1.3.0.tar.gz
    tar xzvf yasm-1.3.0.tar.gz
    cd yasm-1.3.0
    ./configure --prefix="$HOME/ffmpeg_build" --bindir="$HOME/bin"
    make -j6
    make install

    cd ~/ffmpeg_sources
    git clone --depth 1 http://git.videolan.org/git/x264
    cd x264
    PKG_CONFIG_PATH="$HOME/ffmpeg_build/lib/pkgconfig" ./configure --prefix="$HOME/ffmpeg_build" --bindir="$HOME/bin" --enable-static
    make -j6
    make install

    cd ~/ffmpeg_sources
    wget -e use_proxy=yes -e http_proxy=10.8.8.109:502 https://github.com/mstorsjo/fdk-aac/archive/v0.1.6.tar.gz -O fdk-acc-v0.1.6.tar.gz
    tar xzvf fdk-acc-v0.1.6.tar.gz
    cd fdk-aac-0.1.6
    autoreconf -fiv
    ./configure --prefix="$HOME/ffmpeg_build" --disable-shared
    make -j6
    make install

    cd ~/ffmpeg_sources
    wget -e use_proxy=yes -e http_proxy=10.8.8.109:502 http://downloads.sourceforge.net/project/lame/lame/3.100/lame-3.100.tar.gz
    tar xzvf lame-3.100.tar.gz
    cd lame-3.100
    ./configure --prefix="$HOME/ffmpeg_build" --bindir="$HOME/bin" --disable-shared --enable-nasm
    make -j6
    make install

    cd ~/ffmpeg_sources
    git clone https://git.ffmpeg.org/rtmpdump.git
    cd rtmpdump/librtmp
    sed -i 's/prefix=\/usr\/local/prefix=$(HOME)\/ffmpeg_build/' Makefile
    make -j6
    make install

    # 下载编译 ffmpeg
    cd ~/ffmpeg_sources
    wget -e use_proxy=yes -e http_proxy=10.8.8.109:502 https://github.com/FFmpeg/FFmpeg/archive/n3.3.8.tar.gz -O FFmpeg-n3.3.8.tar.gz
    tar zxf FFmpeg-n3.3.8.tar.gz
    cd FFmpeg-n3.3.8/

    # 编译安装 ffmpeg 到 $HOME/bin
    PATH="$HOME/bin:$PATH" PKG_CONFIG_PATH="$HOME/ffmpeg_build/lib/pkgconfig" ./configure \
    --prefix="$HOME/ffmpeg_build" \
    --extra-cflags="-fPIC -I/usr/local/include -I$HOME/ffmpeg_build/include" \
    --extra-ldflags="-lpthread -L$HOME/ffmpeg_build/lib" \
    --bindir="$HOME/bin" \
    --enable-version3 \
    --enable-runtime-cpudetect --disable-iconv \
    --enable-pic --enable-pthreads \
    --disable-shared --enable-static \
    --disable-network --disable-doc \
    --enable-ffmpeg --disable-ffplay --disable-ffserver --enable-ffprobe \
    --enable-gpl --enable-nonfree \
    --enable-libfdk-aac --enable-libmp3lame --enable-librtmp\
    --enable-libx264 --enable-encoder=libx264 --enable-decoder=h264 \
    --disable-debug
    make -j6 && make install

    # 使用 ldd 将依赖库放到与 ffmpeg ffprobe 可执行文件相同的目录下
    例如取
    /root/bin/ffmpeg ffprobe
    /root/ffmpeg_build/lib/librtmp.so.1

编译 nginx
----------

.. code:: bash

    # 安装依赖
    apt-get install -y build-essential libpcre3 libpcre3-dev libssl-dev unzip software-properties-common

    # 下载 nginx 和 nginx-rtmp-module
    wget -e use_proxy=yes -e http_proxy=10.8.8.109:502 https://github.com/nginx/nginx/archive/release-1.15.2.tar.gz -O nginx-v1.15.2.tar.gz
    wget -e use_proxy=yes -e http_proxy=10.8.8.109:502 https://github.com/arut/nginx-rtmp-module/archive/v1.2.1.tar.gz -O nginx-rtmp-module-v1.2.1.tar.gz

    # 编译 nginx 注意 module 版本号
    tar zxf nginx-v1.15.2.tar.gz
    tar zxf nginx-rtmp-module-v1.2.1.tar.gz

    cd nginx-release-1.15.2
    ./auto/configure --prefix=/usr/local/live-gateway \
    --with-http_ssl_module --with-http_stub_status_module --with-http_secure_link_module \
    --with-http_flv_module --with-http_mp4_module --add-module=../nginx-rtmp-module-1.2.1 --with-debug
    make -j6 && make install

    # 使用 ldd 将依赖库放到与 nginx 可执行文件相同的目录下
    例如取
    /usr/local/live-gateway/sbin/nginx


编译 live-gateway
-----------------

.. code:: bash

    # 自动上传到编译服务器版本并拉回本地
    ./scripts/build_project_c65.sh

    # 在编译服务器编译脚本
    ./scripts/build_project_in_c65.sh


自建系统部署
============

目录结构
--------

.. code:: bash

    # 工程配置文件，默认不用动
    /opt/cloudroom/var/lib/crproj/LiveGateway/config.conf

    # 录制文件临时目录
    /opt/cloudroom/var/LiveGateway/nginx/record/$频道号/$录制文件ID/$录制文件内容(未修复)

    # 录制文件最终存放目录
    /opt/cloudroom/var/LiveGateway/nginx/vod/$会议号/$录制文件ID/$录制文件内容(已修复)

    # 上传文件的目录
    /opt/cloudroom/var/LiveGateway/nginx/upload/

    # 日志文件目录，包含 live-gateway 及其守护进程以及 nginx 的日志
    /opt/cloudroom/logs/LiveGateway/

    # 程序主目录，包含 live-gateway-ice live-gateway nginx ffmpeg
    /opt/cloudroom/distrib/LiveGateway/


端口占用
--------

.. code:: bash

    # 默认本地端口占用
    # 8511: RTMP 推拉流端口
    # 8512: HLS 直播和点播端口
    # 8513: 对外 HTTP 服务接口，如提供 java 端增删服务的请求
    # 8514: 对内 HTTP 服务接口，如与 nginx rtmp


清理命令
--------

.. code:: bash

    # 不要直接发送 kill -9 指令，会导致该项目 nginx 组件变为僵尸进程
    kill -TERM $(ps -ef | grep '/distrib/LiveGateway/' | grep -v grep | grep -v vim | awk '{print $2}'

首次部署
--------

准备环境
++++++++

.. code:: bash

    # 上传编译好的文件到自建系统，注意此命令会重启目标自建系统上的 LiveGateway 网关
    ./scripts/upload_project_c65.sh 10.8.8.248

    # 首次安装时要配置下文件，后续除非升级时需要检查，否则不用
    cp /opt/cloudroom/var/lib/crproj/LiveGateway/env-zj-template /opt/cloudroom/var/lib/crproj/LiveGateway/config.conf

配置 Ice
++++++++

将下面的 xml 内容拷贝成 LiveGateway.xml 文件，然后使用 ice grid admin 工具上传至自建系统即可

.. code:: xml

    <?xml version="1.0" encoding="UTF-8" ?>
    <!-- This file was written by IceGrid Admin -->
    <icegrid>
       <application name="LiveGateway">
          <server-template id="IcePatch2">
             <parameter name="instance-name" default="${application}.IcePatch2"/>
             <parameter name="endpoints" default="default"/>
             <parameter name="directory"/>
             <server id="${instance-name}" activation="on-demand" application-distrib="false" exe="icepatch2server">
                <properties>
                   <property name="IcePatch2.InstanceName" value="${instance-name}"/>
                   <property name="IcePatch2.Directory" value="${directory}"/>
                </properties>
                <adapter name="IcePatch2" endpoints="${endpoints}" id="${server}.IcePatch2">
                   <object identity="${instance-name}/server" type="::IcePatch2::FileServer"/>
                </adapter>
                <adapter name="IcePatch2.Admin" endpoints="default" id="${server}.IcePatch2.Admin"/>
             </server>
          </server-template>
          <server-template id="TplLiveGateway">
             <parameter name="serverNo"/>
             <parameter name="moduleName" default="LiveGateway"/>
             <parameter name="categoryName" default="LiveGateway"/>
             <parameter name="privateConfig" default=""/>
             <parameter name="globalConfig" default=""/>
             <parameter name="user" default="crproj"/>
             <parameter name="workingDir" default="/opt/cloudroom/distrib/LiveGateway/live-gateway-ice/"/>
             <parameter name="exePath" default="/opt/cloudroom/distrib/LiveGateway/live-gateway-ice/live-gateway-ice"/>
             <parameter name="mainPy" default="/opt/cloudroom/var/lib/crproj/LiveGateway/config.conf"/>
             <server id="s${serverNo}-${categoryName}" activation="always" exe="${exePath}" pwd="${workingDir}">
                <option>${mainPy}</option>
                <env>LD_LIBRARY_PATH=${workingDir}lib;$LD_LIBRARY_PATH</env>
                <properties>
                   <property name="AdapterIdentity" value="${categoryName}Adapter"/>
                   <property name="Ice.Override.ConnectTimeout" value="60000"/>
                   <property name="Ice.Override.Timeout" value="60000"/>
                   <property name="Ice.Warn.Connections" value="2048"/>
                   <property name="Ice.ThreadPool.Server.Size" value="1"/>
                   <property name="Ice.ThreadPool.Server.SizeMax" value="1024"/>
                   <property name="Ice.ThreadPool.Server.SizeWarn" value="800"/>
                   <property name="Ice.ThreadPool.Client.Size" value="1"/>
                   <property name="Ice.ThreadPool.Client.SizeMax" value="1024"/>
                   <property name="Ice.ThreadPool.Client.SizeWarn" value="800"/>
                   <property name="IceGridAdmin.Password" value="bar"/>
                   <property name="Ice.Default.EndpointSelection" value="Ordered"/>
                   <property name="IceGridAdmin.Username" value="fsboss"/>
                   <property name="IceGridAdmin.Password" value="123456"/>
                   <property name="Logger.Path" value="/tmp/LiveGateway.log"/>
                   <property name="Logger.Level" value="10"/>
                   <property name="PGDB.Host" value="database-master.cloudroom.com"/>
                   <property name="PGDB.Port" value="5432"/>
                   <property name="PGDB.User" value="postgres"/>
                   <property name="PGDB.Password" value="111111"/>
                   <property name="PGDB.Database" value="conference"/>
                   <property name="PGDB.Debug" value=""/>
                   <property name="Logger.Format" value="%(asctime)s %(threadName)s(%(thread)d)    %(name)s(%(levelname)s)    [%(funcName)s]: %(message)s"/>
                </properties>
                <distrib icepatch="${application}.IcePatch2/server"/>
                <adapter name="${categoryName}Adapter" endpoints="default -p 1120" id="${server}.${categoryName}Adapter">
                   <object identity="s${serverNo}/${categoryName}" type="::${moduleName}::${categoryName}" property="Identity"/>
                </adapter>
             </server>
          </server-template>
          <properties id="TraceProp">
             <property name="Ice.Trace.GC" value="2"/>
             <property name="Ice.Trace.Retry" value="2"/>
             <property name="Ice.Trace.Slicing" value="1"/>
             <property name="Ice.Trace.Locator" value="2"/>
             <property name="Ice.Trace.Network" value="3"/>
             <property name="Ice.Trace.Protocol" value="1"/>
             <property name="Ice.Trace.ThreadPool" value="1"/>
          </properties>
          <node name="node-CRServ8888">
             <server-instance template="TplLiveGateway" serverNo="8888"/>
          </node>
       </application>
    </icegrid>

