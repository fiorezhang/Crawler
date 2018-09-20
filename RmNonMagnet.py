# -*- coding:utf-8 -*-
import os
import re
import shutil

dir = r"F:\2017\TMP\Download_epp_40"
#dir = r'.\test'
idx = r'txt'
if os.path.exists(dir):
    dirs = os.listdir(dir)
    for dirc in dirs:
        try:
            print(dirc)
        except Exception as e:
            print(e)
        delete = True
        files = os.listdir(dir+'./'+dirc)
        for filec in files:
            #print(filec)
            #print(filec.split('.')[-1])
            if filec.split('.')[-1] == idx:
                delete = False
        if delete == True:
            shutil.rmtree(dir+'./'+dirc)
            print('==== DELETE ====')
else:
    print("dir not exists")