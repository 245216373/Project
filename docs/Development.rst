编译发布文档
============

.. code:: bash

    # 编译文档并在本地预览
    ./scripts/build_project_docs.sh

    # 发布文档到内网 nginx 服务器
    ./scripts/upload_project_docs.sh


使用 Docker 开发
================

.. code:: bash

    # 生成并修改环境变量配置文件
    ln -s env-template .env

    # 启动并观察其日志
    ./scripts/run_project_in_docker.sh

    # 进入 docker 内部
    ./scripts/login_project_in_docker.sh

    # 停止并删除
    ./scripts/rm_project_in_docker.sh

    # 在 Docker 内调试，先进入 docker 内部
    # 该命令会移除守护进程并在代码目录准备好调试用的环境
    /debug_app.sh

    # 在 Docker 内运行测试代码，先进入 docker 内部
    # 改命令会进入代码目录并准备好 python 环境
    /test_app.sh
    # 然后执行单元测试
    python -m unittest -v tests.test_flask_app_public.TestUpload.test_nas_upload_one_file
    # 一个特殊的文件会测试当前所有用例，需要如下方式调用
    python tests/tests.py


