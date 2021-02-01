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

import urllib.request
from io import BytesIO
import gzip

HEADER={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/14.0.835.163 Safari/535.1'}  
#PROXIE = {'http':'http://221.0.232.13:61202','https':'https://211.86.50.105:61202'}
TIMEOUT = 20

URLROOT = 'https://qqyf66.com/' #https://dz.zhaifulifabu.com:9527/
URLSUB = [
          '', 
          'youfanhao',      #1
          'zhaifuli',       #2
          'xiachedan',      #3
          'zhainanshe',     #4
          'luyilu',         #5
          'qiuchuchu',      #6
          'feilin',         #7
          'Makemodel',      #8
          'youguowang',     #9
          'Graphis',        #10
          'Legbaby',        #11
          'MiiTao',         #12
          'meiyanshe',      #13
          'xiurenwang',     #14
          'boluoshe',       #15
          'Girlt',          #16
          'Tpimage',        #17
          'youmihui',       #18
          'DKGirl',         #19
          'MFStar',         #20
          'Goddes'	    #21
         ]

#传入图片地址，文件名，保存单张图片
def saveImg(imageURL,fileName):
    try: 
        r = urllib.request.Request(imageURL, headers=HEADER)
        u = urllib.request.urlopen(r, timeout=TIMEOUT)
        data = u.read()
        f = open(fileName, 'wb')
        f.write(data)
        f.close()
        return True
    except urllib.error.URLError as e:
        print('TIMEOUT '+imageURL)
        print(e.reason)
        return False
    except Exception as e:
        print('UNKNOWN '+imageURL)
        print(e)
        return False

#多线程获取图片        
def fetchImg(imageURLQueue):
    ret = True
    while True:
        try:
            urlpair = imageURLQueue.get_nowait()
            i = imageURLQueue.qsize()
            #print("Queue Size "+str(i))
            url = urlpair[0]
            filename = urlpair[1]
        except Exception as e:
            #print(e) #当queue空时，这里会打印一行空内容
            break
        #print("-------- -------- Current Thread: "+threading.currentThread().name+", file: "+filename)
        if saveImg(url, filename) == False: #重复几次尝试下载，间隔一段时间，只影响当前线程
            time.sleep(0.2)
            if saveImg(url, filename) == False:
                time.sleep(0.2)
                if saveImg(url, filename) == False:
                    #print("==== ERROR FETCH ==== "+threading.currentThread().name+", file: "+filename)
                    ret = False
                    break
        time.sleep(0.2)
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

#保存描述评分        
def saveComment(comment, rate, fileName):
    try:
        f = open(fileName, "w")
        f.write(comment)
        f.close()
        return True
    except Exception as e:
        print('Error '+fileName)
        print(e)
        return False        

def decodeResponse(response):
    #print(response)
    
    #有段时间网页用zip加密了，需要解密
    if 1:
        ret = response.decode('gbk')
    else:
        buff = BytesIO(response)
        f = gzip.GzipFile(fileobj=buff)
        ret = f.read().decode('gbk')

    #print(ret)
    return ret

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

#获取描述和评分
def getComment(url):
    try: 
        request = urllib.request.Request(url, headers=HEADER)
        response = urllib.request.urlopen(request).read()
        #print(response)
        response = decodeResponse(response)
    
        pattern = re.compile('<article class="article-content">(.*?)</article>', re.S)
        content = re.search(pattern, response).group(1)
        #print(content)
        
        comment = ''
        pattern = re.compile('<p.*?>(.*?)</p>', re.S)
        try:
            items = re.findall(pattern, content)
            for item in items:
                #print(item)
                comment = comment+item
            comment = re.sub('<br>|<br.*?/>', '\n', comment)
            comment = re.sub('(?i)<img.*?src="(http.*?jpg|http.*?png|http.*?jpeg)".*?>', '', comment)
            #print(comment)
        except Exception as e:
            print(e)
            comment = ''
        
        pattern = re.compile('<i class="glyphicon.*?<span>(.*?)</span>', re.S)
        try:
            rate = re.search(pattern, response).group(1)
            #print(rate)
        except Exception as e:
            #print(e)
            rate = 0 #没有评分的话就算0分，不打打印信息了
        
        return comment, rate
    except urllib.error.URLError as e:
        print('ERROR getComment '+url)
        print(e.reason)
        return None
    except Exception as e:
        print('ERROR getComment '+url)
        print(e)
        return None    
        
        

#获取页面信息
def getPage(urlPage):
    try:
        #print(urlPage)
        #获取当前页面所有主题
        request = urllib.request.Request(urlPage, headers=HEADER)
        response = urllib.request.urlopen(request).read()
        #print(response)
        response = decodeResponse(response)
        
        #剥离其它部分，仅保留相关列表
        #<div class="content-wrap">
        #<div class="pagination pagination-multi">
        pattern = re.compile('<div class="content-wrap">(.*?)<div class="pagination pagination-multi">', re.S)
        content = re.search(pattern, response).group(1)
        #print(content)

        #逐个提取主题
        #<h2><a target="_blank" href="/Girlt/2017/0923/3929.html" title="[Girlt]果团网第5期向唯[61P]">[Girlt]果团网第5期向唯[61P]</a></h2>
        pattern = re.compile('<h2>.*?href="(.*?)".*?title="(.*?)".*?</h2>', re.S)
        items = re.findall(pattern, content)#item[0]本地页面地址，需加上urlroot这个网站地址前缀，item[1]标题
        #for item in items:
        #    print(item[0], item[1])
        return items
    except urllib.error.URLError as e:
        print('ERROR getPage '+urlPage)
        print(e.reason)
        return None
    except Exception as e:
        print('ERROR getPage '+urlPage)
        print(e)
        return None

def getAllPages(url):
    url_list = [url]
    url_root = os.path.split(url)[0]
    
    #print(url_root)
    #print(url_list)
    
    while True:
        try:
            #获取当前页面所有主题
            request = urllib.request.Request(url, headers=HEADER)
            response = urllib.request.urlopen(request).read()
            #print(response)
            response = decodeResponse(response)
            
            #<li class='next-page'><a target="_blank" href='list_16_2.html'>下一页</a></li>
            pattern = re.compile('(?i)<li class=.*?next-page.*?href=.(.*?.html).*?</li>', re.S)
            content = re.search(pattern, response).group(1)
            #print(content)
            
            #特殊处理
            if url_root == URLROOT:
                url_root = url_root+'/page' #主页上的下一页链接，中间少了'/page'所以不得不手动加上
            url = url_root+'/'+content
            url_list.append(url)
            #time.sleep(0.2)
        except urllib.error.URLError as e:
            print(e.reason)
            break
        except Exception as e:
            #print(e)
            break
        #print(url_list)
    return url_list
    

#获取当前页图片信息并保存
def getImg(url):
    try: 
        request = urllib.request.Request(url, headers=HEADER)
        response = urllib.request.urlopen(request).read()
        #print(response)
        response = decodeResponse(response)
    
        pattern = re.compile('<article class="article-content">(.*?)</article>', re.S)
        content = re.search(pattern, response).group(1)
        #print(content)
    
        #<p><img src="http://images.zhaofulipic.com:8818/allimg/171013/1556223052-6.jpg" alt="[Girlt]果团网第13期周琰琳"></p>
        content = re.sub('<br>|<br.*?/>', '\n', content)
        pattern = re.compile('(?i)<img.*?src="(http.*?png|http.*?jpeg|http.*?jpg)".*?>')
        items = re.findall(pattern, content)#item图片地址，绝对地址
        #print(items)
        #for item in items:
        #    print(item)
        return items
    except urllib.error.URLError as e:
        print('ERROR getImg '+url)
        print(e.reason)
        return None
    except Exception as e:
        print('ERROR getImg '+url)
        print(e)
        return None
            
            

#爬虫入口
def crawler(urlroot, url, path, threads, hide, clean):
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
                           
    #获取当前分类下所有页面URL
    classPages = getAllPages(url) 
    #print(classPages)  
    if classPages:
        #获取当前分类所有页面的下级信息
        for url_classpage in classPages:
            print('-'*10+url_classpage)
            items = getPage(url_classpage)
            if items:
                for item in items:
                    #time.sleep(0.2)
                    url_firstpage = urlroot+'/'+item[0]
                    title_firstpage = validateTitle(item[1])
                    if hide == 0:
                        print('-'*20+url_firstpage+'-'*10+title_firstpage)
                    else:
                        print('-'*20+url_firstpage)
                    #特殊处理未分类（主页进来的）页面，用url里面的class信息归类到相关的上级目录
                    if path[-1]=='_':
                        classpath = path+item[0].split('/')[1]
                    else:
                        classpath = path
                    #print(classpath)
                    #assert()
                    if mkdir(classpath+os.sep+title_firstpage):
                        Error = False
                        mkdir(classpath+os.sep+title_firstpage+os.sep+'UNFINISHED')#标记未完成
                        comment, rate = getComment(url_firstpage)
                        saveComment(comment, rate, classpath+os.sep+title_firstpage+os.sep+str(rate)+'.txt')
                        singlePages = getAllPages(url_firstpage)
                        if singlePages:
                            i = 1000 #用作图片文件名
                            urlQueue = queue.Queue()
                            for url_singlepage in singlePages:
                                #time.sleep(0.2)
                                #print('-'*30+url_singlepage)
                                imgs = getImg(url_singlepage)
                                if imgs:
                                    for img in imgs:
                                        i = i+1
                                        name_jpg = str(i)+'.jpg'
                                        urlpair = [img, classpath+os.sep+title_firstpage+os.sep+name_jpg]
                                        urlQueue.put(urlpair)
                                else:
                                    Error = True
                            if Error == False:
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
                                #print('TIME ', (endTime-startTime))
                            rmdir(classpath+os.sep+title_firstpage+os.sep+'UNFINISHED')#标记已完成
                        else:
                            Error = True
                            print('Error get '+url_firstpage)
                        if Error:
                            print('REMOVE')
                            rmdir(classpath+os.sep+title_firstpage)
                    else:
                        print('EXIST')
    else:
        print('Error get '+url)

#仅仅用来方便调试
def spider(urlroot, url, path, threads, hide, clean):
    if mkdir(path):
        Error = False
        mkdir(path+os.sep+'UNFINISHED')#标记未完成
        comment, rate = getComment(url)
        saveComment(comment, rate, path+os.sep+str(rate)+'.txt')
        singlePages = getAllPages(url)
        if singlePages:
            i = 1000 #用作图片文件名
            urlQueue = queue.Queue()
            for url_singlepage in singlePages:
                #time.sleep(0.2)
                #print('-'*30+url_singlepage)
                imgs = getImg(url_singlepage)
                if imgs:
                    for img in imgs:
                        i = i+1
                        name_jpg = str(i)+'.jpg'
                        urlpair = [img, path+os.sep+name_jpg]
                        urlQueue.put(urlpair)
                    else:
                        Error = True
            if Error == False:
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
                #print('TIME ', (endTime-startTime))
            rmdir(path+os.sep+'UNFINISHED')#标记已完成
        else:
            Error = True
            print('Error get '+url)
        if Error:
            print('REMOVE')
            rmdir(path)
    else:
        print('EXIST')    
        rmdir(path)
        
def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--spider", type=int, default=0)
    parser.add_argument("--url", type=str, default="")
    parser.add_argument("--folder", type=str, default="")
    parser.add_argument("--index", type=int, default=100)
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--hide", type=int, default=1)
    parser.add_argument("--clean", type=int, default=0)
    args = parser.parse_args()
    return args
    
    
###### Main ######
if __name__ == "__main__":
    args = get_args()
    for idx, item in enumerate(URLSUB):
        print("%4d -- %s" % (idx, item))
    assert(args.index < len(URLSUB))
    
    PATH = 'D:/2017/TMP/Download_YX_'+URLSUB[args.index]
    if args.index == 0:
        URLCRAWLER = URLROOT+'/page/1.html'
    else:
        URLCRAWLER = URLROOT+'/'+URLSUB[args.index]+'/'
    THREADS = args.threads
    HIDE = args.hide
    CLEAN = args.clean
    URLSPIDER = args.url
    PATHSPIDER = 'D:/2017/TMP/Download_YX_'+URLSUB[args.index]+'/'+args.folder
    if args.spider == 0:
        crawler(URLROOT, URLCRAWLER, PATH, THREADS, HIDE, CLEAN)
    else:
        spider(URLROOT, URLSPIDER, PATHSPIDER, THREADS, HIDE, CLEAN)

    try:
        rmdir('D:/2017/TMP/Download_YX_')
    except Exception as e:
        pass

#没保存完的目录，放一张名为unfinished的图片，图片内容也是这个，便于预览查找

