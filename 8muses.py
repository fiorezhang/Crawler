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
def parseImg(url, browser, retry, timeset):
    #print(url)    
    while retry:
        retry -= 1        
        try:
            browser.set_page_load_timeout(timeset)
            browser.get(url)
        except TimeoutException:
            browser.execute_script('window.stop()')
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
            #print(content)
            return content
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

#多线程获取image    
def fetchImg(imageURLQueue, browser):
    ret = True
    #time.sleep(numpy.random.random())

    while True:
        try:
            urlpair = imageURLQueue.get_nowait()
            i = imageURLQueue.qsize()
            #print("Queue Size "+str(i))
            url = urlpair[0]
            filename = urlpair[1]
        except Exception as e:
            #print(e)
            break
        print("-------- -------- Current Thread: "+threading.currentThread().name+", file: "+filename)
        
        retry = 20
        timeset = 1
        imageURL = parseImg(URLROOT+url, browser, retry, timeset)
        while imageURL == None and retry>0:
            retry=retry-1
            timeset = timeset*2
            imageURL = parseImg(url, browser, timeset)
        if retry==0:
            print("==== ERROR PARSE ==== "+threading.currentThread().name+", file: "+filename)
            ret = False
            break
        
        retry = 3
        timeset = 1
        while saveImg("https:"+imageURL, filename, retry, timeset) == False and retry>0:
            time.sleep(1)
            retry=retry-1
            timeset = timeset*2
        if retry==0:
            print("==== ERROR FETCH ==== "+threading.currentThread().name+", file: "+filename)
            ret = False
            break
        #time.sleep(0.5)
    #print("-------- -------- End Thread: "+threading.currentThread().name+" with: ", ret)
    
    return ret
            

class ImgThread(threading.Thread):
    def __init__(self, func, args=()):  
        super(ImgThread,self).__init__()
        self.func = func
        self.args = args

    def run(self):  
        self.result = self.func(*self.args)  
  
    def get_result(self):
        try:
            return self.result  # 如果子线程不使用join方法，此处可能会报没有self.result的错误
        except Exception:
            return None


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
            
            if len(items) == 0:
                break
            url_list.extend(items)
            #print(items)
            break
        except Exception as e:
            print(e)
            #break
    return url_list        
    
#爬虫入口
def crawler(urlroot, path, threads=16, hide=0, clean=1):
    #创建当前分类的目录
    mkdir(path)
    #删除未完成目录
    if clean == 1:
        print('REMOVE UNFINISHED')
        if os.path.exists(path):
            dirs = os.listdir(path)
            for dirc in dirs:
                #try:
                #    print(dirc)
                #except Exception as e:
                #    print(e)
                if os.path.isdir(path+os.sep+dirc):
                    files = os.listdir(path+os.sep+dirc)
                    for filec in files:
                        delete = False
                        if os.path.isdir(path+os.sep+dirc+os.sep+filec):
                            file_2s = os.listdir(path+os.sep+dirc+os.sep+filec)
                            for filec_2 in file_2s:
                                if filec_2 == 'UNFINISHED':
                                    delete = True
                                if filec_2 == 'ERROR':
                                    delete = True
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
            if mkdir(folder_l1) or os.path.exists(folder_l1+os.sep+'!UNFINISHED'):
                mkdir(folder_l1+os.sep+'!UNFINISHED')
                pages_l2 = getAlbums(urlroot+page_l1) #取得第二层，每一个漫画册
                for page_l2 in pages_l2:
                    print("-"*20+page_l2)
                    str_l2 = str_l1+name_l1+"/"
                    name_l2 = page_l2[len(str_l2):]
                    print(" "*20+name_l2)
                    folder_l2 = path+os.sep+validateTitle(name_l1)+os.sep+validateTitle(name_l2)
                    if mkdir(folder_l2):
                        Error = False
                        mkdir(folder_l2+os.sep+'UNFINISHED')
                        imgs_l2 = getPictures(urlroot+page_l2) #取得漫画册每个图片的单独网页，有可能漫画册还有子目录，要再往下一层
                        if len(imgs_l2) == 0:  #再往下一层，取得的图片网页放到同一个list
                            print(" "*30+"NEXT LEVEL"+" "*10+page_l2)
                            pages_l3 = getAlbums(urlroot+page_l2)
                            for page_l3 in pages_l3:
                                imgs_l3 = getPictures(urlroot+page_l3)
                                if len(imgs_l3) == 0:
                                    print(" "*40+"NEXT LEVEL"+" "*10+page_l3)
                                    pages_l4 = getAlbums(urlroot+page_l3)
                                    for page_l4 in pages_l4:
                                        imgs_l4 = getPictures(urlroot+page_l4)
                                        imgs_l3 += imgs_l4
                                imgs_l2 += imgs_l3
                        if len(imgs_l2) == 0: #还没有图片，报错
                            Error = True
                            print('Error get '+page_l2)
                        i = 1000 #用作图片文件名            
                        for img in imgs_l2:
                            print(" "*30+img)
                            i = i+1
                            name_jpg = str(i)+'.jpg'
                            urlpair = [img, folder_l2+os.sep+name_jpg]
                            retry = 20
                            timeset = 1
                            urlImg = parseImg(URLROOT+img, browser, retry, timeset)
                            if urlImg == None:
                                Error = True
                                with open(folder_l2+os.sep+'Error.log', 'a+') as f:
                                    f.write(URLROOT+img+"|"+folder_l2+os.sep+name_jpg+"\n")
                                continue #TODO
                            retry = 10
                            timeset = 2
                            ret = saveImg("https:"+urlImg, folder_l2+os.sep+name_jpg, retry, timeset)
                            if ret == False:
                                Error = True
                                with open(folder_l2+os.sep+'Error.log', 'a+') as f:
                                    f.write(URLROOT+img+"|"+folder_l2+os.sep+name_jpg+"\n")
                                continue #TODO                            
                        if Error:
                            mkdir(folder_l2+os.sep+'ERROR') 
                        rmdir(folder_l2+os.sep+'UNFINISHED')#标记已完成  
                    else:
                        print('EXIST')
                rmdir(folder_l1+os.sep+'!UNFINISHED')#标记已完成         
            else:
                print('EXIST')
    #回收浏览器资源
    for i in range(threads):    
        browser[i].quit()
        
    return

        
def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--hide", type=int, default=1)
    parser.add_argument("--clean", type=int, default=0)
    args = parser.parse_args()
    return args
    
    
###### Main ######
if __name__ == "__main__":
    args = get_args()
    
    THREADS = args.threads
    HIDE = args.hide
    CLEAN = args.clean

    crawler(URLROOT, PATH, THREADS, HIDE, CLEAN)
    

#没保存完的目录，放一张名为unfinished的图片，图片内容也是这个，便于预览查找

