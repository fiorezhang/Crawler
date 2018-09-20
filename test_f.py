# -*- coding:utf-8 -*-
import urllib.request
import re
import os

#传入图片地址，文件名，保存单张图片
def saveImg(imageURL,fileName):
    TIMEOUT = 60

    header={  
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.137 Safari/537.36 LBBROWSER'  
        }  

    try: 
        r = urllib.request.Request(imageURL, headers=header)
        u = urllib.request.urlopen(r, timeout=TIMEOUT)
        data = u.read()
        f = open(fileName, 'wb')
        f.write(data)
        f.close()
        return True
    except urllib.error.URLError as e:
        print('==== TIMEOUT ====    '+imageURL)
        print(e.reason)
        return False


IMGURL = 'http://s2.img26.com/2018/03/14/0920db1901972683865.jpg'  #can not
#IMGURL = 'http://i.imagseur.com/uploads/2018-03/14/bf9f3ce131971aa0fb579421e9624a65.jpg'  #can

saveImg(IMGURL, './temp.jpg')