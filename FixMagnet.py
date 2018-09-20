# -*- coding:utf-8 -*-
import os
import re

f_path = r"F:\2017\TMP\Download_38"
#f_path = r'.'
def find_file(file_path, lis):
    ls = os.listdir(file_path)
    for i in ls:
        son_path = os.path.join(file_path,i)
        if os.path.isdir(son_path):
            find_file(son_path,lis)
        else:
            file_post = str(i.split('.')[-1])
            if file_post == r'txt':
                lis.append(i)
                #剥离种子内多余字符
                content = loadMagnet(son_path)
                #print(content)
                content = re.sub(r'<span>|</span>|</b>|<br/>', r'', content)
                saveMagnet(content, son_path)
                #重命名文件 一次性使用
                file_son_path = son_path.split('\\')[-1]
                path_son_path = ''
                for item in son_path.split('\\')[:-1]:
                    path_son_path = path_son_path + item
                    path_son_path = path_son_path + '\\'
                #print(file_son_path)
                #print(path_son_path)
                new_son_path = re.search(r'^[\d]{2}-[\d]{2} (.*)', file_son_path)
                if new_son_path:
                    os.rename(son_path, path_son_path+new_son_path.group(1))
                    #print(path_son_path+new_son_path.group(1))
                #print('modified{srcnam}'.format(srcnam=son_path))
    return lis

def saveMagnet(content,fileName):
    try:
        f = open(fileName,"wb")
        f.write(content.encode('utf-8'))
        f.close()
        return True
    except Exception as e:
        print('==== TX ERROR ==== '+fileName+' ==== '+content)
        print(e)
        return False
        
def loadMagnet(fileName):
    try:
        f = open(fileName, 'r')
        c = f.read()
        f.close()
        return c
    except Exception as e:
        print('==== RX ERROR ==== '+fileName)
        print(e)
        return None
        


if __name__ == "__main__":
    print('Modified: ',find_file(f_path, []))