# -*- coding:utf-8 -*-
import urllib.request
import re
import os
import argparse
import shutil
import time
import numpy
import threading
import queue 
import ssl
import sys

#urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed
ssl._create_default_https_context = ssl._create_unverified_context

HEADER={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.137 Safari/537.36 LBBROWSER'}  
#PROXIE = {'http':'http://221.0.232.13:61202','https':'https://211.86.50.105:61202'}
TIMEOUT = 5

class Logger(object):
    def __init__(self, filename="Default.log"):
        self.terminal = sys.stdout
        self.log = open(filename, "a")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        pass
    
#=======================================================================   
#传入图片地址，文件名，保存单张图片
def saveImg(imageURL,fileName,timeSet=0):
    if timeSet == 0:
        timeSet = TIMEOUT
    try: 
        r = urllib.request.Request(imageURL, headers=HEADER)
        u = urllib.request.urlopen(r, timeout=timeSet)
        data = u.read()
        u.close()
        f = open(fileName, 'wb')
        f.write(data)
        f.close()
        return True
    #except urllib.error.URLError as e:
    #    print('==== TIMEOUT ====    '+str(timeSet)+'    ====    '+imageURL)
    #    print(e.reason)
    #    return False
    except Exception as e:
        print('==== UNKNOWN ====    '+str(timeSet)+'    ====    '+imageURL)
        print(e)
        return False

#多线程获取image    
def fetchImg(imageURLQueue):
    ret = True
    time.sleep(numpy.random.random())
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
        #print("-------- -------- Current Thread: "+threading.currentThread().name+", file: "+filename)
        retry = 3
        timeset = 2
        while saveImg(url, filename, timeset) == False and retry>0:
            time.sleep(1)
            retry=retry-1
            timeset = timeset*2
        if retry==0:
            #print("==== ERROR FETCH ==== "+threading.currentThread().name+", file: "+filename)
            ret = False
            break
        #time.sleep(0.5)
    #print("-------- -------- End Thread: "+threading.currentThread().name+" with: ", ret)
    return ret


#传入图片地址，文件名，保存单张图片
def savePageImg(pageURL,fileName,timeSet=0):
    if timeSet == 0:
        timeSet = TIMEOUT
    try:
        #获取当前页面所有主题
        request = urllib.request.Request(pageURL, headers=HEADER)
        handle = urllib.request.urlopen(request, timeout=timeSet)
        content = handle.read().decode('utf-8')
        handle.close()
        #print(content)
        
        #full&quot;:&quot;
        pattern = re.compile('full&quot;:&quot;(.*?jpg|.*?png)', re.S)
        urlJpg = re.search(pattern, content).group(1)
        #print(urlJpg)
        if "http" not in urlJpg:
            urlJpg = "https:"+urlJpg
        imageURL = urlJpg
    except Exception as e:
        print('==== ERROR   ====    '+str(timeSet)+'    ====    '+pageURL)
        print(e)
        return False
    try: 
        r = urllib.request.Request(imageURL, headers=HEADER)
        u = urllib.request.urlopen(r, timeout=timeSet)
        data = u.read()
        u.close()
        f = open(fileName, 'wb')
        f.write(data)
        f.close()
        return True
    #except urllib.error.URLError as e:
    #    print('==== TIMEOUT ====    '+str(timeSet)+'    ====    '+imageURL)
    #    print(e.reason)
    #    return False
    except Exception as e:
        print('==== UNKNOWN ====    '+str(timeSet)+'    ====    '+imageURL)
        print(e)
        return False

#多线程获取image    
def fetchPageImg(imageURLQueue):
    ret = True
    time.sleep(numpy.random.random())
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
        #print("-------- -------- Current Thread: "+threading.currentThread().name+", file: "+filename)
        retry = 3
        timeset = 2
        while savePageImg(url, filename, timeset) == False and retry>0:
            time.sleep(1)
            retry=retry-1
            timeset = timeset*2
        if retry==0:
            #print("==== ERROR FETCH ==== "+threading.currentThread().name+", file: "+filename)
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
    rstr = r"[\/\\\:\*\?\"\<\>\|\ \.]"  # '/ \ : * ? " < > |'
#    rstr = r"[\*\?\"\<\>\|]"  # '/ \ : * ? " < > |'
    new_title = re.sub(rstr, r"-", title)  # 替换为下划线
    new_title = new_title[:200] # 防止过长文件名
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
#=======================================================================       

def getAllPages(urlroot, url):
    urllist = [url]
    #print(url, urlroot)
    while True:
        print("-",end="")
        sys.stdout.flush()
        try:
            #获取当前页面所有主题
            request = urllib.request.Request(url, headers=HEADER)
            handle = urllib.request.urlopen(request, timeout=TIMEOUT)
            content = handle.read().decode('utf-8')
            handle.close()
            #print(content)
            
            pattern = re.compile('<ul class="pagination">(.*?)</ul>', re.S)
            content = re.search(pattern, content).group(1)
            #print(content)
            
            #<a rel="next" href="/series/2">Next ›</a>
            pattern = re.compile('<a rel="next" href="(.*?)">', re.S)
            content = re.search(pattern, content).group(1)
            #print(content)
            
            url = urlroot+'/'+content
            urllist.append(url)
            #time.sleep(0.2)
        except Exception as e:
            print(e)
            break
        #print(urllist) 
        
        #仅供测试时不要一下取得所有页面
        #if len(urllist)>1:
        #    break
    print("")
    return urllist
    
def getAllPagesOneshoot(urlroot, url):
    urllist = [url]
    #print(url, urlroot)
    
    try:
        #获取当前页面所有主题
        request = urllib.request.Request(url, headers=HEADER)
        handle = urllib.request.urlopen(request, timeout=TIMEOUT)
        content = handle.read().decode('utf-8')
        handle.close()
        #print(content)
        
        pattern = re.compile('<ul class="pagination">(.*?)</ul>', re.S)
        content = re.search(pattern, content).group(1)
        #print(content)
        
        #<a href="/series/original-work/page/2367">Last &raquo;</a>
        pattern = re.compile('<a href="(.*?)">Last &raquo;</a>')
        content = re.search(pattern, content).group(1)
        #print(content)
        
        if content:
            urlGroupIndex = content.split('/')[:-1]
            urlIndex = ''
            for item in urlGroupIndex:
                urlIndex += item+'/'
            urlMax = int(content.split('/')[-1])
            #print(urlIndex)
            #print(urlMax)
            for i in range(1, int(content.split('/')[-1])):
                urllist.append(urlroot+'/'+urlIndex+'/'+str(i+1))

        #time.sleep(0.2)
    except Exception as e:
        print(e)
            
    #print(urllist) 
        
        #仅供测试时不要一下取得所有页面
        #if len(urllist)>1:
        #    break
    return urllist    

def getSerials(urlroot, url):
    try:
        #获取当前页面所有主题
        request = urllib.request.Request(url, headers=HEADER)
        handle = urllib.request.urlopen(request, timeout=TIMEOUT)
        content = handle.read().decode('utf-8')
        handle.close()
        #print(content)
       
        #<h3 class="series-title"><a href="https://www.simply-hentai.com/series/fate-stay-night">Series</a></h3>
        pattern = re.compile('<h3 class="series-title"><a href="(.*?)">Series</a></h3>')
        items = re.findall(pattern, content)
        
        #time.sleep(0.2)
    except Exception as e:
        print(e)
        return []
    #print(items)                
    return items            

def getAlbums(urlroot, url):
    try:
        #获取当前页面所有主题
        request = urllib.request.Request(url, headers=HEADER)
        handle = urllib.request.urlopen(request, timeout=TIMEOUT)
        content = handle.read().decode('utf-8')
        handle.close()
        #print(content)
       
        #<div class="image-container"><a title=".hack//SIGN" class="js-overview-link" href="https://www.simply-hentai.com/hack/hacksign">
        pattern = re.compile('<div class="image-container">.*?<a title="(.*?)" class="js-overview-link" href="(.*?)">', re.S)
        items = re.findall(pattern, content)
        
        #time.sleep(0.2)
    except Exception as e:
        print(e)
        return []
    #print(items)                
    return items                

def getAllImgs(urlroot, url, urlSerial):
    urllist = []
    urlAlbum = url
    #print(url, urlroot)
    
    #从album获取第一张图片所在页面
    try:
        #获取当前页面所有主题
        request = urllib.request.Request(url, headers=HEADER)
        handle = urllib.request.urlopen(request, timeout=TIMEOUT)
        content = handle.read().decode('utf-8')
        handle.close()
        #print(content)
        
        pattern = re.compile('<a class="image-preview".*?href="(.*?)">', re.S)
        content = re.search(pattern, content).group(1)
        #print(content)
        
        #time.sleep(0.2)
    except Exception as e:
        print(e)   
    
    urlCurrent = content
    urlLast = ""
    #print(url)
        
    #从第一张图片页面开始，提取图片url，并获取下一张图片的页面
    while True:
        print(".",end="")
        sys.stdout.flush()
        try:
            #获取当前页面所有主题
            request = urllib.request.Request(urlCurrent, headers=HEADER)
            handle = urllib.request.urlopen(request, timeout=TIMEOUT)
            content = handle.read().decode('utf-8')
            handle.close()
            #print(content)
            
            #full&quot;:&quot;
            pattern = re.compile('full&quot;:&quot;(.*?jpg)', re.S)
            urlJpg = re.search(pattern, content).group(1)
            #print(urlJpg)
            if "http" not in urlJpg:
                urlJpg = "https:"+urlJpg
            urllist.append(urlJpg)
            
            pattern = re.compile('path&quot;:&quot;(.*?)&quot', re.S)
            urlNextGroup = re.findall(pattern, content)
            #print(urlNextGroup)
            findNext = False
            for urlNext in urlNextGroup:
                if urlNext != urlCurrent and urlNext != urlSerial and urlNext != urlAlbum and urlNext != urlLast:
                    urlLast = urlCurrent
                    urlCurrent = urlNext
                    findNext = True
                    break
            #print("urlCurrent: " + urlCurrent)
            #print("urlLast:" + urlLast)
            
            if findNext is False:
                break

            #time.sleep(0.2)
        except Exception as e:
            print(e)    
            break

    print("")
    #print(urllist)            
    return urllist

def getAllImgsOnshoot(urlroot, url):
    urlOneshoot = url+'/all-pages'

    try:
        #获取当前页面所有主题
        request = urllib.request.Request(urlOneshoot, headers=HEADER)
        handle = urllib.request.urlopen(request, timeout=TIMEOUT)
        content = handle.read().decode('utf-8')
        handle.close()
        #print(content)
        
        #<a class="image-preview" href="https://www.simply-hentai.com/original-work/kemomimi-danshi-to-love-hame-douchuuki-d867d/page/10678161">
        pattern = re.compile('<a class="image-preview" href="(.*?)">', re.S)
        items = re.findall(pattern, content)
        
    except Exception as e:
        print(e)
        return []

    return items
    

#爬虫入口
def crawler(urlroot, url, path, threads, hide, clean):
    timeCurrent = time.strftime("%H-%M-%S", time.localtime())
    sys.stdout = Logger("./hs_"+timeCurrent+".log")
    print("LOG RELOCATED") # this is should be saved in yourlogfilename.txt

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
                delete = False
                if os.path.isdir(path+os.sep+dirc):
                    files = os.listdir(path+os.sep+dirc)
                    for filec in files:
                        if filec == 'UNFINISHED':
                            delete = True
                    if delete == True:
                        shutil.rmtree(path+os.sep+dirc)
                        if hide == 0:
                            try:
                                print('DELETE '+dirc)
                            except Exception as e:
                                pass
        else:
            print("Dir not exists")  

    pages = getAllPagesOneshoot(urlroot, url)
    print("Total Pages: ", len(pages))
    for page in pages:
        print('-'*5 + page)
        serials = getSerials(urlroot, page)
        for serial in serials:
            print('-'*10 + serial)
            pagesSerial = getAllPagesOneshoot(urlroot, serial)
            print("Current Pages: ", len(pagesSerial))
            for pageSerial in pagesSerial:
                print('-'*15 + pageSerial)
                albums = getAlbums(urlroot, pageSerial)
                for album in albums:
                    title = urllib.request.unquote(album[1].split('/')[-1]) #避免重复，用url最末段当目录名
                    if title=='':
                        title = urllib.request.unquote(album[1].split('/')[-2])
                    title = validateTitle(title) #不用album[0]，因为原始命名有重复等原因
                    urlAlbum = album[1]
                    print('-'*20 + urlAlbum)
                    if mkdir(path+os.sep+title):
                        Error = False
                        mkdir(path+os.sep+title+os.sep+'UNFINISHED')#标记未完成
                        i = 1000 #用作图片文件名
                        urlQueue = queue.Queue()
                        pageImgs = getAllImgsOnshoot(urlroot, urlAlbum)
                        if pageImgs:
                            for pageImg in pageImgs:
                                i = i+1
                                name_jpg = str(i)+'.jpg'
                                urlpair = [pageImg, path+os.sep+title+os.sep+name_jpg]
                                urlQueue.put(urlpair)
                        else:
                            Error = True
                        if Error == False:
                            startTime = time.time()
                            ths = []
                            thn = threads
                            for _ in range(0, thn):
                                t = ImgThread(fetchPageImg, args=(urlQueue,))
                                ths.append(t)
                            for t in ths:
                                t.start()
                            for t in ths:
                                t.join()
                            for t in ths:
                                if t.get_result() == False: 
                                    Error = True
                            endTime = time.time()
                            #print('TIME ', (endTime-startTime))
                        rmdir(path+os.sep+title+os.sep+'UNFINISHED')#标记已完成
                        if Error:
                            print('REMOVE')
                            rmdir(path+os.sep+title)
                    else:
                        print('EXIST')        
    

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
    URLROOT = "https://www.simply-hentai.com"
    URLSUB = "series"
    PATH = 'F:/2017/TMP/Download_SH'
    URLCRAWLER = URLROOT+'/'+URLSUB
    THREADS = args.threads
    HIDE = args.hide
    CLEAN = args.clean

    crawler(URLROOT, URLCRAWLER, PATH, THREADS, HIDE, CLEAN)
