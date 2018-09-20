# -*- coding:utf-8 -*-
import os
import re


def find_file(file_path):
    ls = os.listdir(file_path)
    for i in ls:
        son_path = os.path.join(file_path,i)
        if os.path.isdir(son_path):
            print(son_path)
            new_son_path = ''.join(x for x in son_path if ord(x) < 256)
            print(new_son_path)
            os.rename(son_path, new_son_path)

    
if __name__ == "__main__":
    f_path = r'.\Download_boluoshe'    
    find_file(f_path)    
