# -*- coding:utf-8 -*-
import platform
import urllib.request
import re
import os
import argparse
import shutil
import time
import numpy
import threading
import queue
from selenium import webdriver
from selenium.common.exceptions import TimeoutException

UNFINISHED="00000000"
#ERROR = "99999999"
ERRLOG = "99999999.log"

HEADER={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.137 Safari/537.36 LBBROWSER'}  
#PROXIE = {'http':'http://221.0.232.13:61202','https':'https://211.86.50.105:61202'}
TIMEOUT = 10


URLROOT = 'https://www.8muses.com'

if 'Windows' in platform.platform():
    PATH = 'F:/2017/TMP/Download_8Muses'
    PHANTOMJS_PATH = r'C:\Users\FioreZ\.anaconda\phantomjs-2.1.1-windows\bin\phantomjs.exe'
else:
    PATH = '/home/ftp_root/server/temp/Download_8Muses'
    PHANTOMJS_PATH = '/home/phantomjs/bin/phantomjs'



#获取当前页图片信息并保存
contentLast = None
def parseImg(url, browser, retry, timeset):
    global contentLast
    #print(url)    
    while retry:
        retry -= 1        
        try:
            browser.set_page_load_timeout(timeset)
            browser.get(url)
        except TimeoutException:
            browser.execute_script('window.stop()')
            timeset += 1
        source = browser.page_source #获取网页源代码

        pattern = re.compile('<div class="photo"(.*?)</div>')
        contents = re.search(pattern, source)
        if contents != None:
            content = contents.group(1)
            #print(content)
        else:
            print('==== PARSEIMG 1 ====    '+url)
            continue

        pattern = re.compile('<img src="(.*?jpg)"')
        contents = re.search(pattern, content)
        if contents != None:
            content = contents.group(1)
            if content != contentLast:
                contentLast = content
                #print(content)
                return content
            else:
                print('==== PARSEIMG 3 ====    '+url)
                continue
        else:
            print('==== PARSEIMG 2 ====    '+url)
            continue
    return None

        
#传入图片地址，文件名，保存单张图片
def saveImg(imageURL, fileName, retry, timeset):
    while retry:
        retry -= 1       
        try: 
            r = urllib.request.Request(imageURL, headers=HEADER)
            u = urllib.request.urlopen(r, timeout=timeset)
            data = u.read()
            f = open(fileName, 'wb')
            f.write(data)
            f.close()
            return True
        #except urllib.error.URLError as e:
        #    print('==== TIMEOUT ====    '+str(timeSet)+'    ====    '+imageURL)
        #    print(e.reason)
        #    return False
        except Exception as e:
            print('==== SAVEIMG ====    '+imageURL)
            print(e)
    return False


#保存文件时候, 去除名字中的非法字符
def validateTitle(title):
    rstr = r"[\/\\\:\*\?\"\<\>\|]"  # '/ \ : * ? " < > |'
#    rstr = r"[\*\?\"\<\>\|]"  # '/ \ : * ? " < > |'
    new_title = re.sub(rstr, r"_", title)  # 替换为下划线
    return new_title
     
#创建新目录
def mkdir(path):
    path = path.strip()
    # 判断路径是否存在
    # 存在     True
    # 不存在   False
    isExists=os.path.exists(path)
    #print(isExists)
    # 判断结果
    if not isExists:
        # 如果不存在则创建目录
        # 创建目录操作函数
        os.makedirs(path)
        return True
    else:
        # 如果目录存在则不创建，并提示目录已存在
        return False     

#删除目录
def rmdir(path):
    shutil.rmtree(path)

#获取当前页面下图库页面信息
def getAlbums(url):
    url_list = []
        
    page = 1
    while True:
        try:
            #获取当前页面所有主题
            #print("[P] "+url+'/'+str(page))
            request = urllib.request.Request(url+'/'+str(page), headers=HEADER)
            response = urllib.request.urlopen(request, timeout=3).read().decode('utf-8', 'ignore')
            #print(response)
            
            pattern = re.compile('<a class="c-tile t-hover" href="(.*?/album/.*?)">')
            items = re.findall(pattern, response)

            for i, item in enumerate(items):
                item = item.split('"')[-1]
                items[i] = item
            
            if len(items) == 0:
                break
            url_list.extend(items)
            #print(items)
            page += 1
            #time.sleep(1)
        except Exception as e:
            print(e)
            #break
    return url_list        

#获取当前页面下图片页面信息
def getPictures(url):
    url_list = []

    while True:
        try:
            #获取当前页面所有主题
            #print("[I] "+url+'/'+str(page))
            request = urllib.request.Request(url, headers=HEADER)
            response = urllib.request.urlopen(request, timeout=3).read().decode('utf-8', 'ignore')
            #print(response)
            
            pattern = re.compile('<a class="c-tile t-hover" href="(.*?/picture/.*?)">')
            items = re.findall(pattern, response)
            
            for i, item in enumerate(items):
                item = item.split('"')[-1]
                items[i] = item
            
            if len(items) == 0:
                break
            url_list.extend(items)
            #print(items)
            break
        except Exception as e:
            print(e)
            #break
    return url_list        
    
def getAllPictures(urlroot, page):
    imgs = []
    imgs += getPictures(urlroot+page)
    pages = getAlbums(urlroot+page)
    for page in pages.copy():
        imgs += getPictures(urlroot+page)
        print(" "*30+"NEXT LEVEL"+" "*10+page)
        pages = getAlbums(urlroot+page)
        for page in pages.copy():
            imgs += getPictures(urlroot+page)
            print(" "*40+"NEXT LEVEL"+" "*10+page)
            pages = getAlbums(urlroot+page)
            for page in pages.copy():
                imgs += getPictures(urlroot+page)
                #print(" "*50+"NEXT LEVEL"+" "*10+page)
                #pages = getAlbums(urlroot+page)
    return imgs
    
    
#爬虫入口
def crawler(urlroot, path, threads, hide, clean, fix):
    #创建当前分类的目录
    mkdir(path)
    #删除未完成目录
    if clean == 1:
        print('REMOVE UNFINISHED')
        if os.path.exists(path):
            dirs = os.listdir(path)
            for dirc in dirs:
                if os.path.isdir(path+os.sep+dirc):
                    files = os.listdir(path+os.sep+dirc)
                    for filec in files:
                        delete = False
                        if os.path.isdir(path+os.sep+dirc+os.sep+filec):
                            file_2s = os.listdir(path+os.sep+dirc+os.sep+filec)
                            for filec_2 in file_2s:
                                if filec_2 == UNFINISHED:
                                    delete = True
                                #if filec_2 == ERRLOG:
                                #    delete = True
                            if delete == True:
                                shutil.rmtree(path+os.sep+dirc+os.sep+filec)
                                if hide == 0:
                                    try:
                                        print('DELETE '+dirc+os.sep+filec)
                                    except Exception as e:
                                        pass
        else:
            print("Dir not exists")    

    #利用PhantomJS加载网页
    browser = webdriver.PhantomJS(executable_path=PHANTOMJS_PATH)
    browser.set_page_load_timeout(30) # 最大等待时间

    #从根节点开始解析网页
    page_l0 = "/comics"
    pages_l1 = getAlbums(urlroot+page_l0) #取得第一层，大的漫画系列
    for page_l1 in pages_l1:
        print("-"*10+page_l1)
        str_l1 = "/comics/album/"
        if str_l1 in page_l1:
            name_l1 = page_l1[len(str_l1):]
            print(" "*10+name_l1)
            folder_l1 = path+os.sep+validateTitle(name_l1)
            if (fix != 1 and mkdir(folder_l1)) or os.path.exists(folder_l1+os.sep+UNFINISHED):
                mkdir(folder_l1+os.sep+UNFINISHED)
                pages_l2 = getAlbums(urlroot+page_l1) #取得第二层，每一个漫画册
                for page_l2 in pages_l2:
                    print("-"*20+page_l2)
                    str_l2 = str_l1+name_l1+"/"
                    name_l2 = page_l2[len(str_l2):]
                    print(" "*20+name_l2)
                    folder_l2 = path+os.sep+validateTitle(name_l1)+os.sep+validateTitle(name_l2)
                    ret = mkdir(folder_l2)
                    if (ret == True and fix == 0) or (ret == False and fix == 1):
                        Error = False
                        mkdir(folder_l2+os.sep+UNFINISHED)
                        imgs_l2 = getAllPictures(urlroot, page_l2)
                        i = 1000 #用作图片文件名            
                        urlImgLast = None
                        for img in imgs_l2:
                            i = i+1
                            name_jpg = str(i)+'.jpg'
                            if fix == 1 and os.path.exists(folder_l2+os.sep+name_jpg):
                                continue
                            timeCurrent = time.strftime("%H:%M:%S", time.localtime())
                            print(" "*30+name_jpg+" "*5+timeCurrent+" "*5+img)  
                            #urlpair = [img, folder_l2+os.sep+name_jpg]
                            retry = 20
                            timeset = 1
                            urlImg = parseImg(URLROOT+img, browser, retry, timeset)
                            if urlImg == None:
                                Error = True
                                with open(folder_l2+os.sep+ERRLOG, 'a+') as f:
                                    f.write(URLROOT+img+"|"+folder_l2+os.sep+name_jpg+"\n")
                                continue #TODO
                            retry = 10
                            timeset = 2
                            ret = saveImg("https:"+urlImg, folder_l2+os.sep+name_jpg, retry, timeset)
                            if ret == False:
                                Error = True
                                with open(folder_l2+os.sep+ERRLOG, 'a+') as f:
                                    f.write(URLROOT+img+"|"+folder_l2+os.sep+name_jpg+"\n")
                                continue #TODO                            
                        #if Error:
                        #    mkdir(folder_l2+os.sep+ERROR) 
                        rmdir(folder_l2+os.sep+UNFINISHED)#标记已完成  
                    elif ret == False:
                        print('EXIST')
                    else:
                        rmdir(folder_l2)
                        print('IGNORE')
                if fix != 1:
                    rmdir(folder_l1+os.sep+UNFINISHED)#标记已完成         
            else:
                print('EXIST')
    #回收浏览器资源
    browser.quit()
        
    return

def fixerrlog(errorlog):
    #利用PhantomJS加载网页
    browser = webdriver.PhantomJS(executable_path=PHANTOMJS_PATH)
    browser.set_page_load_timeout(30) # 最大等待时间
    
    result = True
    
    with open(errorlog, 'r') as f:
        lines = f.readlines()
        for line in lines:
            print(line)
            url, file = line.split("|")
            file = file[:-1] #remove "\n"
            print(url)
            print(file)
            retry = 40
            timeset = 4
            urlImg = parseImg(url, browser, retry, timeset)
            if urlImg == None:
                print("ERROR")
                result = False
                continue
            retry = 20
            timeset = 8
            ret = saveImg("https:"+urlImg, file, retry, timeset)
            if ret == False:
                print("ERROR")
                result = False
                contiune
            print("PASS")
    
    if result == True:
        print("ALL PASS")
        os.remove(errorlog)
    browser.quit()
        
def clearduplicate():
    path = PATH
    if os.path.exists(path):
        dirs = os.listdir(path)
        for dirc in dirs:
            if os.path.isdir(path+os.sep+dirc):
                files = os.listdir(path+os.sep+dirc)
                for filec in files:
                    sizeLast = 0
                    if os.path.isdir(path+os.sep+dirc+os.sep+filec):
                        file_2s = os.listdir(path+os.sep+dirc+os.sep+filec) 
                        file_2s.sort(key= lambda x:int(x[:-4]))
                        for filec_2 in file_2s:
                            if os.path.splitext(filec_2)[1] == '.jpg':
                                size = os.path.getsize(path+os.sep+dirc+os.sep+filec+os.sep+filec_2)
                                if size != sizeLast:
                                    sizeLast = size
                                else:
                                    print("REMOVE:    " + path+os.sep+dirc+os.sep+filec+os.sep+filec_2)
                                    os.remove(path+os.sep+dirc+os.sep+filec+os.sep+filec_2)

def test(path):
    if path != "":
        imgs = getAllPictures(URLROOT, path)
        for img in imgs:
            print(img)
    else:
        print("EMPTY PATH")
        
def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--hide", type=int, default=1)
    parser.add_argument("--clean", type=int, default=0)
    parser.add_argument("--fix", type=int, default=0)
    parser.add_argument("--test", type=int, default=0)
    parser.add_argument("--errorlog", type=str, default="")
    parser.add_argument("--cleardup", type=int, default=0)
    args = parser.parse_args()
    return args
    
    
###### Main ######
if __name__ == "__main__":
    args = get_args()
    
    THREADS = args.threads
    HIDE = args.hide
    CLEAN = args.clean
    FIX = args.fix
    TEST = args.test
    ERRORLOG = args.errorlog
    CLEARDUP = args.cleardup
    
    if TEST == 1:
        path = input("Test path: ")
        test(path)
    elif ERRORLOG != "":
        fixerrlog(ERRORLOG)
    elif CLEARDUP == 1:
        clearduplicate()
    else:
        crawler(URLROOT, PATH, THREADS, HIDE, CLEAN, FIX)


#没保存完的目录，放一张名为unfinished的图片，图片内容也是这个，便于预览查找

