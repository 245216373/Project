公共部分
========

鉴权规则
--------

约定鉴权格式为 md5，双方通讯格式为 http json，无论 GET 或者 POST 请求

鉴权 t 为时间戳格林秒，每次请求生成

md5key 为 11111111111111110000000011111111

可选的 随机数 nonce 为 6 位如 132456  不传时不参与计算

sign 为32位鉴权值

可选的 sign_type 固定为 md5  不传时默认为 md5

鉴权内容 sign_content 为 除 sign 和 sign_type 以外的所有 请求参数

.. code:: python

    # 假如 请求内容 如下(其中 a b c 仅仅为模拟业务参数(可选) nonce sign_type 可选)：
    {
        'a': 1, 'b': 2, 'c': 3, 't': 12345678, 'nonce': 123456, 'sign': 'xxx', 'sign_type': 'md5'
    }

    # 则 鉴权内容 如下
    'a=1&b=2&c=3&nonce=123456&t=12345678'

生成和校验 sign = md5($sign_content + $md5key)

公共字段
--------

可选的 _id 字段，该字段由发起者侧生成的全局唯一标识，用来标识交易的唯一性


推流直播点播
============

自建系统 10.8.8.248 为例

推流地址
--------

支持 rtmp 协议推流：

rtmp://ip:port/live/$(channel_id)?t=xxx&sign_type=md5&sign=xxx&nonce=xxx&meeting_id=xxx&expire_t&业务参数

channel_id 频道号 鉴权时需要将其也列为 channel_id=$(channel_id) 进行拼接

t 时间戳

可选的 sign_type 签名类型

sign 签名计算方法参考公共部分的鉴权规则

可选的 nonce 签名计算方法参考公共部分的鉴权规则

可选的 meeting_id 可选的会议参数，设置时录像将会按照会议号存储，并且日志中也会以其为标识

expire_t 推流过期时间，为时间戳格林秒，过期后再次推流将会拒绝

推流地址由 **web** 端生成，生成后发给用户，用户可以使用该地址用如 OBS 直接推流，也可以告知给 MAccess 让它推

最全如： rtmp://10.8.8.248:8511/live/9551_10000881?t=xxx&sign_type=md5&sign=xxx&nonce=xxx&meeting_id=10000881&expire_t=xxx&a=1&b=2

最精简如： rtmp://10.8.8.248:8511/live/9551_10000881?t=xxx&sign=xxx&expire_t=xxx 鉴权串： channel_id=9551_10000881&expire_t=xxx&t=xxx


直播地址
--------
支持 rtmp 和 hls 协议，直播不做鉴权：

RTMP: rtmp://10.8.8.248:8511/live/9551_10000881

HLS: http://10.8.8.248:8512/live/9551_10000881.m3u8

点播地址
--------

只支持 m3u8，点播不做鉴权：

由视频信息查询接口返回，类似如下：

http://ip:port/vod/会议号(可能没有)/录制文件ID/index.m3u8

存在会议号时如： http://10.8.8.248:8512/vod/10000881/39b896271d374853bd2cf245900ee9d1/index.m3u8

或无会议号时如： http://10.8.8.248:8512/vod/39b896271d374853bd2cf245900ee9d1/index.m3u8

Client
======

公共部分
--------

请求公共头

_id=$(uuid)&t=xxx&sign_type=md5&sign=xxx&nonce=xxx

其中 _id sign_type nonce 可以没有

服务端接口模拟接收本机模拟器
----------------------------

联调时需将其更改为对方接口地址

http://localhost:8080/web_simulator


申请推流权限接口(暂不实现)
--------------------------

POST ?event_type=auth_publish&channel_id=xxx&meeting_id=xxx&其它原有参数

返回 200 OK 则表示允许推流

返回 403 则表示禁止

推流开始通知接口
----------------

POST ?event_type=notify_publish&channel_id=xxx&meeting_id=xxx&其它原有参数

返回 200 OK 则表示通知成功处理

推流完成通知接口
----------------

POST ?event_type=notify_publish_done&channel_id=xxx&meeting_id=xxx&其它原有参数

返回 200 OK 则表示通知成功处理


录制完成通知接口
----------------

POST ?event_type=notify_record_done&channel_id=xxx&meeting_id=xxx&其它原有参数

上送内容 {"file_id": "abcd", "file_type": "m3u8", 参考 查询文件信息接口 的其它字段}

返回 200 OK 则表示通知成功处理


上传文件转码完成通知接口
------------------------

POST ?event_type=notify_transcode_upload_file_done&meeting_id=xxx&其它原有参数

上送内容，转码后文件 {"file_id": "abcd", "file_type": "m3u8", "task_id": "xxx", 参考 查询文件信息接口 的其它字段}

返回 200 OK 则表示通知成功处理


文件裁剪完成通知接口
--------------------

POST ?event_type=notify_cut_vod_file_done&meeting_id=xxx&其它原有参数

上送内容，裁剪后文件 {"file_id": "abcd", "file_type": "m3u8", "task_id": "xxx", 参考 查询文件信息接口 的其它字段}

返回 200 OK 则表示通知成功处理


文件拼接完成通知接口
--------------------

POST ?event_type=notify_merge_vod_file_done&meeting_id=xxx&其它原有参数

上送内容，裁剪后文件 {"file_id": "abcd", "file_type": "m3u8", "task_id": "xxx", 参考 查询文件信息接口 的其它字段}

返回 200 OK 则表示通知成功处理


上传完成通知接口
----------------

POST ?event_type=notify_upload_file_done

上送内容

.. code:: python

    {"error_code": 0, "error_info": "", "task_id": "xxx", "file_id": "abcd", "file_type": "mp4"}

返回 200 OK 则表示通知成功处理

Server
======

公共部分
--------

返回 200 OK 则表示接口成功处理，但仍需要检查 error_code，当 error_code 不为数字 0 时，error_info 字段标识错误

返回其它错误则失败


查询文件信息接口
----------------

GET http://ip:port?_id=xxx&t=xxx&sign_type=md5&sign=xxx&nonce=xxx&action_type=info_record_file&file_id=abcd&file_type=m3u8

如： http://10.8.8.248:8513?t=xxx&sign=xxx&action_type=info_record_file&file_id=xxx&file_type=m3u8

返回格式：

.. code:: python

    # 文件创建时间 开始时间 结束时间 时长 文件类型 文件大小(KB) 单双通道 高清 快照图片 
    {
        "error_code": 0, "error_info": "", "play_url": "xxx", "file_size": "111111",
        "create_time": 1539682756, "record_begin_time": 1539682756, "record_end_time": 1539682796, "record_time_lenght": 40,
        "audio_channel": 2, "resolution": "720", "snapshot_url": "xxx.jpeg"
    }

删除文件接口
------------

POST http://ip:port?_id=xxx&t=xxx&sign_type=md5&sign=xxx&nonce=xxx&meeting_id=xxx&action_type=delete_record_file&file_id=xxx&file_type=m3u8

如： http://10.8.8.248:8513?t=xxx&sign=xxx&action_type=delete_record_file&file_id=xxx&file_type=m3u8

返回格式：

.. code:: python

    {"error_code": 0, "error_info": ""}


文件上传转码接口
----------------

POST http://ip:port?_id=xxx&t=xxx&sign_type=md5&sign=xxx&nonce=xxx&meeting_id=xxx&action_type=transcode_upload_file&file_id=xxx&file_type=m3u8&transcode_args={jsonstr}

如： http://10.8.8.248:8513?t=xxx&sign=xxx&action_type=transcode_upload_file&file_id=xxx&file_type=mp4&transcode_args={jsonstr}

file_id： 文件上传完成通知的 id

file_type： 文件上传完成通知的 type

transcode_args： 如下：

.. code:: python

    transcode_args = {
        "template_type": 1,  # 模板 类型
        "s": "1280x720",  # 分辨率
        "r": 24,  # 帧率
        "crf": 34,  # 质量
        "file_id": "xxx", # 输出文件 ID 可选参数
        "file_type": "m3u8", # 输出文件类型
    }


返回格式：

.. code:: python

    {"error_code": 0, "error_info": "", "task_id": "xxx"}


文件裁剪接口
------------

POST http://ip:port?_id=xxx&t=xxx&sign_type=md5&sign=xxx&nonce=xxx&meeting_id=xxx&action_type=cut_vod_file&file_id=xxx&file_type=m3u8&transcode_args={jsonstr}

如： http://10.8.8.248:8513?t=xxx&sign=xxx&action_type=cut_vod_file&file_id=xxx&file_type=m3u8&cut_args={jsonstr}

file_id： 源文件的 ID

file_type： 源文件的类型

cut_args： 如下：

.. code:: python

    cut_args = {
        "template_type": 1,  # 模板 类型 可选，默认为 1
        "ss": 0,  # 秒开始
        "t": 10,  # 截取多少秒
        "file_id": "xxx", # 输出文件 ID 可选参数
        "file_type": "m3u8", # 输出文件类型
    }


返回格式：

.. code:: python

    {"error_code": 0, "error_info": "", "task_id": "xxx"}


文件拼接接口
------------

POST http://ip:port?_id=xxx&t=xxx&sign_type=md5&sign=xxx&nonce=xxx&meeting_id=xxx&action_type=merge_vod_file&file_id=xxx&file_type=m3u8&transcode_args={jsonstr}

如： http://10.8.8.248:8513?t=xxx&sign=xxx&action_type=merge_vod_file&file_id=xxx&file_type=m3u8&merge_args={jsonstr}

file_id： 源文件的 ID

file_type： 源文件的类型

merge_args： 如下：

.. code:: python

    merge_args = {
        "template_type": 1,  # 模板 类型 可选，默认为 1
        "file_id": "xxx",  # 输出文件 ID 可选参数
        "merge_files": [  # 其它拼接的文件，从第二个开始计算
            {
                "file_id": "bbb",
                "file_type": "m3u8",
            },
            {
                "file_id": "ccc",
                "file_type": "m3u8",
            },
            {
                "file_id": "ccc",  # 可重复
                "file_type": "m3u8",
            },
            ...
        ],
    }


返回格式：

.. code:: python

    {"error_code": 0, "error_info": "", "task_id": "xxx"}



文件切片上传接口
----------------

参考 http://fex.baidu.com/webuploader/ 官方手册

切片上传地址： POST http://ip:port/upload/accept?file=文件域&task_id=xxx&chunk=0

.. code:: python

    {"error_code": 0, "error_info": ""}

切片上传成功后回调地址： GET http://ip:port/upload/complete?task_id=xxx&file_type=mp4&file_id=xxx

file_id： 可以由前端指定，也可以没有该字段由后端使用 uuid 生成

file_type： 为用户指定的上传文件类型，目前支持 flv mp4 wav 等单独媒体格式

.. code:: python

    {"error_code": 0, "error_info": ""}

文件删除地址： POST http://ip:port/upload/delete?file_type=mp4&file_id=xxx
http://10.8.8.247:8513/upload/delete?file_type=mp4&file_id=test
.. code:: python

    {"error_code": 0, "error_info": ""}
