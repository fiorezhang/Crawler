# -*- coding:utf-8 -*-
import os
import re
import shutil

#保存文件时候, 去除名字中的非法字符
def validateTitle(title):
    rstr = r"[\/\\\:\*\?\"\<\>\|.]"  # '/ \ : * ? " < > |'
#    rstr = r"[\*\?\"\<\>\|]"  # '/ \ : * ? " < > |'
    new_title = re.sub(rstr, r"_", title)  # 替换为下划线
    return new_title

#去掉文件或目录尾部的[xxp]字样
def normalizeTitle(title):
    #abc[xyz] -> abc
    if title[-1] == ']' and (title[-2] == 'p' or title[-2] == 'P'):
        bracketLeft = title.rfind('[')
        if bracketLeft > 0:
            title = title[:bracketLeft]
    #abc【xyz】 -> abc    
    if title[-1] == '】' and (title[-2] == 'p' or title[-2] == 'P'):
        bracketLeft = title.rfind('【')
        if bracketLeft > 0:
            title = title[:bracketLeft]
    #abc［xyz］ -> abc    
    if title[-1] == '］' and (title[-2] == 'p' or title[-2] == 'P'):
        bracketLeft = title.rfind('［')
        if bracketLeft > 0:
            title = title[:bracketLeft]
    return title.rstrip()

def find_file(file_path):
    ls = os.listdir(file_path)
    for i in ls:
        son_path = os.path.join(file_path,i)
        if os.path.isdir(son_path) and i != normalizeTitle(validateTitle(i)):
            print(son_path)
            #new_son_path = ''.join(x for x in son_path if ord(x) < 256)
            new_son_path = os.path.join(file_path, normalizeTitle(validateTitle(i)))
            print(new_son_path)
            if not os.path.isdir(new_son_path):
                os.rename(son_path, new_son_path)
            else:
                shutil.rmtree(son_path)

    
if __name__ == "__main__":
    f_path = r'D:\2017\TMP\Download_EPP_wangyouzipai'    
    find_file(f_path)    
