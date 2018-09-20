#coding=utf-8

import urllib.request





item = "http://slide.sports.sina.com.cn/g/slide_2_730_181437.html#p=1"
title = urllib.request.unquote(item.split('/')[-1])
if title == '':
    title = urllib.request.unquote(item.split('/')[-2])
print(title)
print("中文")