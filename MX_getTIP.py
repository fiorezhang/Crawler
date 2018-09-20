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
import sys, io

#设置url请求的头
HEADER={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.137 Safari/537.36 LBBROWSER'}  
#PROXIE = {'http':'http://221.0.532.13:61202','https':'https://211.86.50.105:61202'}
TIMEOUT = 20

#设置print函数的输出编码格式，避免utf输出报错（默认可能是gbk之类的格式）
#sys.stdout = io.TextIOWrapper(sys.stdout.buffer,encoding='utf8') #改变标准输出的默认编码  


#保存image
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

#多线程获取image    
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
            #print(e)
            break
        #print("-------- -------- Current Thread: "+threading.currentThread().name+", file: "+filename)
        retry = 3
        while saveImg(url, filename) == False and retry>0:
            time.sleep(2)
            retry=retry-1
        if retry==0:
            #print("==== ERROR FETCH ==== "+threading.currentThread().name+", file: "+filename)
            ret = False
            break
        #time.sleep(0.5)
    #print("-------- -------- End Thread: "+threading.currentThread().name+" with: ", ret)
    return ret
            
#线程类
class ImgThread(threading.Thread):
    def __init__(self, func, args=()):  
        super(ImgThread,self).__init__()
        self.func = func
        self.args = args

    def run(self):  
        self.result = self.func(*self.args)  
  
    def get_result(self):
        try:
            return self.result
        except Exception:
            return None

#正则化目录
def validateTitle(title):
    rstr = r"[\/\\\:\*\?\"\<\>\|]"  # '/ \ : * ? " < > |'
#    rstr = r"[\*\?\"\<\>\|]"  # '/ \ : * ? " < > |'
    new_title = re.sub(rstr, r"_", title)  #替换非法字符
    new_title = new_title[:100]#截取过长目录名
    return new_title
     
#创建目录
def mkdir(path):
    path = path.strip()
    isExists=os.path.exists(path)
    #print(isExists)
    if not isExists:
        os.makedirs(path)
        return True
    else:
        return False     

#删除目录
def rmdir(path):
    shutil.rmtree(path)


#获得页面
def getPage(urlPage):
    try:
        #print(urlPage)
        request = urllib.request.Request(urlPage, headers=HEADER)
        response = urllib.request.urlopen(request).read().decode('utf-8', 'ignore')
        #print(response)
        
        pattern = re.compile('<ul id="infinite-articles"(.*?)</ul>', re.S)
        content = re.search(pattern, response)
        if content:
            content = content.group(1)
        #print(content)

        pattern = re.compile('<h2.*?href="(.*?)".*?</h2>')
        items = re.findall(pattern, content)
        #for item in items:
        #    print(item)
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
    i = 0
    #print(url_list)
    
    while True:
        try:
            request = urllib.request.Request(url, headers=HEADER)
            response = urllib.request.urlopen(request).read().decode('utf-8', 'ignore')
            #print(response)
            
            pattern = re.compile('(?i)<a class="nextpostslink".*?href="(http:.*?)".*?</a>', re.S)
            content = re.search(pattern, response)
            if content:
                content = content.group(1)
            #print(content)
            
            if content:
                url = content
                url_list.append(url)
                i+=1
                print('getAllPages '+str(i))
                #time.sleep(0.5)
            else:
                break
        except urllib.error.URLError as e:
            print('ERROR getAllPages '+url)
            print(e.reason)
            break
        except Exception as e:
            print('ERROR getAllPages '+url)
            print(e)
            break
    return url_list
    

#获得图片信息
def getImg(url):
    try: 
        request = urllib.request.Request(url, headers=HEADER)
        response = urllib.request.urlopen(request, timeout=TIMEOUT).read().decode('utf-8', 'ignore')
        #print(response)
    
        pattern = re.compile('<article>(.*?)</article>', re.S)
        content = re.search(pattern, response).group(1)
        #print(content)
    
        pattern = re.compile("(?i)<a href='(http.*?png|http.*?jpeg|http.*?jpg)'.*?/a>")
        items = re.findall(pattern, content)
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

def getAllPages_(url):
    urllist = []
    for i in range(1061):
        url = 'http://www.modelx.org/page/'+str(i+1)+'/'
        urllist.append(url)
    return urllist
            

def getTip(urlPage):
    try:
        #print(urlPage)
        request = urllib.request.Request(urlPage, headers=HEADER)
        response = urllib.request.urlopen(request).read().decode('utf-8', 'ignore')
        #print(response)
        
        pattern = re.compile('<ul id="infinite-articles"(.*?)</ul>', re.S)
        content = re.search(pattern, response)
        if content:
            content = content.group(1)
        #print(content)

        pattern = re.compile('<a href="(.*?)" class="tiptipBlog"')
        items = re.findall(pattern, content)
        #for item in items:
        #    print(item)
        return items
    except urllib.error.URLError as e:
        print('ERROR getPage '+urlPage)
        print(e.reason)
        return None
    except Exception as e:
        print('ERROR getPage '+urlPage)
        print(e)
        return None            

#爬虫入口
def crawler(urlroot, url, path, threads, hide, clean):
    URLSUB = [
              'just-nude',                                          #0
              'nude-in-public',                                     #1
              'coccozella-nudist-photography',                      #2
              'photodromm',                                         #3
              'met-art/met-art-models-a-z',                         #4
              'met-art/met-art-multiple-amateurs',                  #5
              'steamgirl',                                          #6
              'teenfuns',                                           #7
              'zishy-beautiful-girl',                               #8
              'affect3d-comics',                                    #9
              'asian-exclusive/asianude4u',                         #10
              'asian-exclusive/theblackalle',                       #11
              'asian-exclusive/88square',                           #12
              'asian-exclusive/asian-4-you-2/asian-4-you',          #13
              'asian-exclusive/asian-4-you-2/asian4you-cd11-cd20',  #14
              'asian-exclusive/asian-4-you-2/asian4you-cd21-cd30',  #15
              'asian-exclusive/asian-4-you-2/asian4you-cd31-cd40',  #16
              'asian-exclusive/asian-4-you-2/asian4you-cd41-cd52',  #17
              'litu100',                                            #18
              'japanese-av-idols/feti-style',                       #19
              'japanese-av-idols/fever-boy',                        #20
              'japanese-av-idols/first-gravure',                    #21
              'japanese-av-idols/graphis-gals',                     #22
              'japanese-av-idols/limited-edition',                  #23
              'japanese-av-idols/special-contents',                 #24
              'cute-asian-girls',                                   #25
              'graphis-collection-2002-2018',                       #26
              'x-city',                                             #27
              'amour-angels/amour-angels-2006',                     #28
              'amour-angels/amour-angels-2007',                     #29
              'amour-angels/amour-angels-2008',                     #30
              'amour-angels/amour-angels-2009',                     #31
              'amour-angels/amour-angels-2010',                     #32
              'amour-angels/amour-angels-2011',                     #33
              'amour-angels/amour-angels-2012',                     #34
              'femjoy-nude-art/femjoy-2011',                        #35
              'femjoy-nude-art/femjoy-2012',                        #36
              'femjoy-nude-art/femjoy-2013',                        #37
              'femjoy-nude-art/femjoy-2014',                        #38
              'rylsky-art/rylskyart-2013',                          #39
              'rylsky-art/rylskyart-2014',                          #40
              'zemani-gallery-a',                                   #41
              'hentai-anime/hentai-doujin-manga',                   #42
              'hentai-anime/justice-hentai',                        #43
              'hentai-anime/comics-hentai-3d-art',                  #44
              
              'metcn',                                              #45
              '8teenies',                                           #46
              'nude-naked-beach-party',                             #47
              'hippiegoddess',                                      #48
              'older-women',                                        #49
              'actiongirls',                                        #50
              'jordan-carver',                                      #51
              'cosplay',
              'gravure-idols',

              'videos',
              'download/hentai-anime-download',
              'download/jav-torrent',
             ]

    #获取所有页面
    classPages = getAllPages_(url)
    #print(classPages)  
    if classPages:
        #获取下级页面信息
        for url_classpage in classPages:
            print('-'*10+url_classpage)
            tipurls = getTip(url_classpage)
            for tipurl in tipurls:
                tip = tipurl[len('http://www.modelx.org/category/'):-1]
                if tip not in URLSUB:
                    print(tip)
                    URLSUB.append(tip)
    else:
        print('Error get '+url)
    print(URLSUB)


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", type=int, default=100)
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--hide", type=int, default=1)
    parser.add_argument("--clean", type=int, default=0)
    args = parser.parse_args()
    return args
    
    
###### Main ######
if __name__ == "__main__":
    args = get_args()
    URLROOT = 'http://www.modelx.org/'

    PATH = 'F:/2017/TMP/Download_ModelX_'
    URLCRAWLER = URLROOT
    THREADS = args.threads
    HIDE = args.hide
    CLEAN = args.clean
    crawler(URLROOT, URLCRAWLER, PATH, THREADS, HIDE, CLEAN)

