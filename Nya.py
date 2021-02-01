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

#urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed
ssl._create_default_https_context = ssl._create_unverified_context

HEADER={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.137 Safari/537.36 LBBROWSER'}  

TIMEOUT = 10



#传入图片地址，文件名，保存单张图片
def saveImg(imageURL,fileName,timeSet=0):
    #print(imageURL)
    ret = False
    error_1 = None
    error_2 = None
    if timeSet == 0:
        timeSet = TIMEOUT
        
    try: 
        r = urllib.request.Request(imageURL, headers=HEADER)
        u = urllib.request.urlopen(r, timeout=timeSet)
        data = u.read()
        f = open(fileName, 'wb')
        f.write(data)
        f.close()
        ret = True
        return ret
    except Exception as e:
        #print('==== UNKNOWN ====    '+str(timeSet)+'    ====    '+imageURL)
        #print(e)
        error_1 = e

    try: 
        #尝试给图片换一个后缀
        imageURL_head = imageURL[:-3]
        imageURL_tail = imageURL[-3:]
        if imageURL_tail == 'jpg':
            imageURL_swap = imageURL_head + 'png'
        if imageURL_tail == 'png':
            imageURL_swap = imageURL_head + 'jpg'
        r = urllib.request.Request(imageURL_swap, headers=HEADER)
        u = urllib.request.urlopen(r, timeout=timeSet)
        data = u.read()
        f = open(fileName, 'wb')
        f.write(data)
        f.close()
        ret = True
        return ret
    except Exception as e:
        #print('==== UNKNOWN_REFERER ====    '+str(timeSet)+'    ====    '+imageURL)
        #print(e)
        error_2 = e      

    print('==== UNKNOWN ====    '+str(timeSet)+'    ====    '+imageURL)
    print(error_1, error_2)      
    return ret
    

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
        retry = 2
        timeset = 15
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

#保存magnet
def saveMagnet(content,fileName):
    try:
        f = open(fileName,"wb")
        f.write(content.encode('utf-8'))
        f.close()
        return True
    except Exception as e:
        print('==== FAIL ====    '+content)
        print(e)
        return False

#保存标记
def saveFlag(content, fileName):
    try:
        f = open(fileName, "ab")
        f.write(content.encode('utf-8'))
        f.close()
        return True
    except Exception as e:
        print('==== FAIL ====    '+content)
        print(e)
        return False

#读取标记
def loadFlag(fileName):
    try:
        f = open(fileName, "r+")
        content = f.read()
        return content
    except Exception as e:
        print('==== FAIL ====    ')
        print(e)
        return None

#保存文件时候, 去除名字中的非法字符
def validateTitle(title):
    rstr = r"[\t\/\\\:\*\?\"\<\>\|.]"  # '/ \ : * ? " < > |'
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

#获取页面信息
def getPage(url, num):
    #直接生成单页url
    urlPage = url + '/g/' + str(num) + '/list2/'
    #print(urlPage)
    try:
        #获取当前页面所有主题
        request = urllib.request.Request(urlPage, headers=HEADER)
        response = urllib.request.urlopen(request, timeout=TIMEOUT).read().decode('utf-8')
        #print(response)
        
        #剥离其它部分，仅保留相关列表
        #<title>[同人誌H漫畫](C83) [NARUHO堂 (なるほど)] 木の葉の性処理係 (NARUTO -ナルト-) [中国翻訳] [カラー化] [無修正] &raquo; 喵紳士NyaHentai:免费中文A漫</title>
        pattern = re.compile('<title>(.*?) &raquo; 喵紳士NyaHentai:免费中文A漫</title>', re.S)
        content = re.search(pattern, response).group(1)
        #print(content)
        title = content[8:] #去掉[同人誌H漫畫]

        return urlPage, title
    #except urllib.error.URLError as e:
    #    print('==== TIMEOUT ====    '+urlPage)
    #    print(e.reason)
    #    return None
    except Exception as e:
        print('==== UNKNOWN ====    '+urlPage)
        print(e)
        return None

#获取最新页面编号
def getPageLast(url):
    urlPage = url
    try:
        #获取当前页面所有主题
        request = urllib.request.Request(urlPage, headers=HEADER)
        response = urllib.request.urlopen(request, timeout=TIMEOUT).read().decode('utf-8')
        #print(response)
                
        pattern = re.compile('<div class="container index-container">(.*?)<div class="caption">', re.S)
        content = re.search(pattern, response).group(0)
        #print(content)

        #data-src="https://i0.nyacdn.com/galleries/1806632/1.jpg" onerror=
        pattern = re.compile('<a href="/g/(.*?)/" class="cover target-by-blank"')
        content = re.search(pattern, content).group(1)
        #print(content)

        return content
    #except urllib.error.URLError as e:
    #    print('==== TIMEOUT ====    '+urlPage)
    #    print(e.reason)
    #    return None
    except Exception as e:
        print('==== UNKNOWN ====    '+urlPage)
        print(e)
        return None    

#获取当前页图片信息并保存
def getImg(url):
    try: 
        request = urllib.request.Request(url, headers=HEADER)
        response = urllib.request.urlopen(request, timeout=TIMEOUT).read().decode('utf-8')
        #print(response)
    
        pattern = re.compile('<section id="image-container"(.*?)</section>', re.S)
        content = re.search(pattern, response).group(0)
        #print(content)
    
        #data-src="https://i0.nyacdn.com/galleries/1806632/1.jpg" onerror=
        pattern = re.compile('data-src="(http.*?jpg|http.*?png)" onerror')
        items = re.findall(pattern, content)#item图片地址，绝对地址
        
        #print(items)
        #for item in items:
        #    print(item)
        return items
    #except urllib.error.URLError as e:
    #    print('==== TIMEoUT ====    '+url)
    #    print(e.reason)
    #    return None
    except Exception as e:
        print('==== UNKNOWN ====    '+url)
        print(e)
        return None

#爬虫入口
def crawler(urlroot, url, start, end, revert, flagretry, updateonly, path, threads, clean, lang):
    mkdir(path)
    #删除未完成目录
    if clean == 1:
        print('==== REMOVE UNFINISHED ====')
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
                        try:
                            print('==== DELETE ====    '+dirc)
                        except Exception as e:
                            print('==== DELETE ====')
        else:
            print("dir not exists")    
    

    
    #生成指定页面范围
    if flagretry == 1:
        pageList = loadFlag(path+os.sep+'FLAG.txt').split(' ')[:-1] #去掉末尾空格
        pageList = list(set(map(eval, pageList)))
        pageList.sort()
        os.remove(path+os.sep+'FLAG.txt')
        for n in pageList:
            saveFlag(str(n)+' ', path+os.sep+'FLAG.txt')
    elif updateonly == 1:
        pageLastNew = int(getPageLast(url))
        pageLastOld = int(loadFlag(path+os.sep+'PAGE.txt').split(' ')[0]) #去掉末尾空格
        assert(pageLastOld <= pageLastNew)
        print("==== UPDATED PAGES ====    " + str(pageLastOld) + "    -    " + str(pageLastNew))
        pageList = list(range(pageLastOld, pageLastNew+1))
        if revert == 1:
            pageList.reverse()     
    else:
        assert(start >= 1 and start <= end)
        pageList = list(range(start, end+1))
        if revert == 1:
            pageList.reverse()         
    print(pageList)
    
    #return
    
    #遍历指定页面
    #for num in range(start-1, end):
    for num in pageList:
        print('-'*10+"==== HON ", num, " ===="+'-'*40)

        retryPage = 3
        while retryPage >0:
            try:
                urlId, title = getPage(url, num) #num start from 1
                break
            except:
                pass
            retryPage -= 1
        if retryPage > 0:
            if (not '[進行中]' in title) and (not '[进行中]' in title) and (lang in title): #只下载感兴趣的语言（通过文件名是否包含特殊字段）
                retrySuccess = False
                folder = validateTitle(title)
                #打印当前要下载的链接信息
                try:
                    print('-'*20+urlId, folder)
                except:
                    print('-'*20+urlId)
                    
                if mkdir(path+'./'+folder):
                    Error = False

                    imgs = getImg(urlId)
                    if (imgs):
                        mkdir(path+os.sep+folder+os.sep+'UNFINISHED')#标记未完成
                        #下载图片
                        i = 1000
                        #多线程处理， 线程数即参数
                        if threads > 0:
                            urlQueue = queue.Queue()
                            for img in imgs:
                                i=i+1
                                jpgname = str(i)+'.jpg'
                                urlpair = [img, path+os.sep+folder+os.sep+jpgname]
                                urlQueue.put(urlpair)
                            startTime = time.time()
                            ths = []
                            thn = threads
                            for _ in range(0, thn):
                                t = ImgThread(fetchImg, args=(urlQueue,))
                                ths.append(t)
                            for t in ths:
                                t.start()
                            for t in ths:
                                t.join()
                            for t in ths:
                                if t.get_result() == False: 
                                    Error = True
                            endTime = time.time()
                            #print('-------- -------- TIME: ', (endTime-startTime))
                        #单线程处理
                        else:
                            for img in imgs:
                                i=i+1
                                jpgname = str(i)+'.jpg'
                                if saveImg(img, path+os.sep+folder+os.sep+jpgname) == False:
                                    if saveImg(img, path+os.sep+folder+os.sep+jpgname) == False:
                                        Error = True
                                        break
                        time.sleep(1) #DELAY
                        rmdir(path+os.sep+folder+os.sep+'UNFINISHED')#标记已完成
                    else:
                        Error = True
                        try: 
                            print('==== ERROR ====    '+folder)
                        except:
                            print('==== ERROR ====    '+urlId)
                                                   
                    if Error == True:
                        rmdir(path+os.sep+folder)
                        saveFlag(str(num)+' ', path+os.sep+'FLAG.txt') #单独记录下载失败的编号
                        try:
                            print('==== REMOVE ====    '+folder)
                        except:
                            print('==== REMOVE ====    '+urlId)
                    else:
                        if flagretry == 1:
                            retrySuccess = True
                else:
                    try:
                        print('==== EXIST ====    '+urlId, folder)   
                    except:
                        print('==== EXIST ====    '+urlId)  
                    if flagretry == 1:
                        retrySuccess = True
                if flagretry == 1: 
                    pageListCurrent = loadFlag(path+os.sep+'FLAG.txt').split(' ')[:-1]
                    pageListCurrent = list(set(map(eval, pageListCurrent)))
                    pageListCurrent.sort()
                    if retrySuccess == True:
                        pageListCurrent.remove(num)
                    os.remove(path+os.sep+'FLAG.txt')
                    for n in pageListCurrent:
                        saveFlag(str(n)+' ', path+os.sep+'FLAG.txt')
            else:
                print('==== LANG MISMATCH ====    '+urlId)
        else:
            print('==== NULL ====    '+ str(num))
    if flagretry == 1: 
        pageListCurrent = loadFlag(path+os.sep+'FLAG.txt').split(' ')[:-1]
        pageListCurrent = list(set(map(eval, pageListCurrent)))
        pageListCurrent.sort()
        os.remove(path+os.sep+'FLAG.txt')
        for n in pageListCurrent:
            saveFlag(str(n)+' ', path+os.sep+'FLAG.txt')
    elif updateonly == 1:
        os.remove(path+os.sep+'PAGE.txt')
        saveFlag(str(pageLastNew)+' ', path+os.sep+'PAGE.txt')    
       
def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=1)
    parser.add_argument("--revert", type=int, default=1)
    parser.add_argument("--flagretry", type=int, default=0)
    parser.add_argument("--updateonly", type=int, default=0)
    parser.add_argument("--threads", type=int, default=0)
    parser.add_argument("--clean", type=int, default=0)
    parser.add_argument("--lang", type=int, default=0)
    args = parser.parse_args()
    return args

language = ["", "中国翻訳"]

###### Main ######
if __name__ == "__main__":
    args = get_args()
    URLROOT = 'https://zha.doghentai.com'
    URLCRAWLER = 'https://zha.doghentai.com'
    PATH = 'D:/2017/TMP/Download_Nya'
    START = args.start
    END = args.end
    REVERT = args.revert
    FLAGRETRY = args.flagretry
    UPDATEONLY = args.updateonly
    THREADS = args.threads
    CLEAN = args.clean
    LANG = language[args.lang]
    crawler(URLROOT, URLCRAWLER, START, END, REVERT, FLAGRETRY, UPDATEONLY, PATH, THREADS, CLEAN, LANG)

#没保存完的目录，放一张名为unfinished的图片，图片内容也是这个，便于预览查找