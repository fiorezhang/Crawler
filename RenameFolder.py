# -*- coding:utf-8 -*-
import os
import re
import shutil

def find_file(file_path):
    ls = os.listdir(file_path)
    for i in ls:
        son_path = os.path.join(file_path,i)
        if os.path.isdir(son_path) and i[2] == '-' and i[5] == ' ':
            print(son_path)
            #new_son_path = ''.join(x for x in son_path if ord(x) < 256)
            new_son_path = os.path.join(file_path, i[6:])
            print(new_son_path)
            if not os.path.isdir(new_son_path):
                os.rename(son_path, new_son_path)
            else:
                shutil.rmtree(son_path)

    
if __name__ == "__main__":
    f_path = r'F:\2017\TMP\Download_EPP_12'    
    find_file(f_path)    
