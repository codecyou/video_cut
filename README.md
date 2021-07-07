videoCutGUI  界面化程序 可以直接拖拽文件，但注意：有图形符号的时候可能会出错，编解码解不了图形字符
version 1.0.0.1
    update:
        1.输入裁剪开始时间和结束点用秒数单位（s）

version 1.0.0.2
    update:
        1.输入裁剪开始时间和结束点用时间段单位（xHxMxs）,直接输入时分秒，不用自己计算总秒数
        2.新增get_float_value函数用于获取输入框值
        3.设置线程守护

version 1.0.0.3
    update:
        1.优化代码，调整界面
        2.增加任务追加功能，可以一次性添加多个任务，单线程顺序执行任务，不用像之前版本要等操作完才能添加新任务

注意：当前程序使用moviepy模块有个bug：如果是手机录屏 码率很高的时候，裁剪操作时一定要指定视频帧率，不然就会出现几百万帧的视频压制！
使用方法：
方式一：
源码运行
需要pip安装windnd,moviepy
然后python videoCutGui.py即可
方式二：
直接下载打包好的程序
解压videoCutGUI.1.0.0.3.rar执行videoCutGUI.exe即可

![video_cut使用说明 2021-07-07_082501](https://user-images.githubusercontent.com/71281805/124682876-6f949500-defe-11eb-8e68-556a572de5dc.jpg)
