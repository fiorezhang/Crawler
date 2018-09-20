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

#保存文件时候, 去除名字中的非法字符
def validateTitle(title):
    rstr = r"[\/\\\:\*\?\"\<\>\|\.]"  # '/ \ : * ? " < > |'
#    rstr = r"[\*\?\"\<\>\|]"  # '/ \ : * ? " < > |'
    new_title = re.sub(rstr, r"_", title)  # 替换为下划线
    #print(title)
    #print(new_title)
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

    

#获得图片信息
def getImg(url):
    try: 
        request = urllib.request.Request(url, headers=HEADER)
        response = urllib.request.urlopen(request, timeout=TIMEOUT).read().decode('utf-8', 'ignore')
        #print(response)
    
        pattern = re.compile('<div class="view-content">(.*?)<div class="row row-15"', re.S)
        content = re.search(pattern, response).group(1)
        #print(content)
    
        #pattern = re.compile('(?i)<img.*?content="(.*?.jpg)"',re.S)
        pattern = re.compile('(?i)<img.*?src="(.*?)"')
        items = re.findall(pattern, content)
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
            
def getTitle(url):
    try: 
        request = urllib.request.Request(url, headers=HEADER)
        response = urllib.request.urlopen(request, timeout=TIMEOUT).read().decode('utf-8', 'ignore')
        #print(response)
    
        pattern = re.compile('<meta name="subject" content="(.*?)" />')
        content = re.search(pattern, response).group(1)
        #print(content)

        return content
    except urllib.error.URLError as e:
        print('ERROR getImg '+url)
        print(e.reason)
        return None
    except Exception as e:
        print('ERROR getImg '+url)
        print(e)
        return None

#爬虫入口
def crawler(urlroot, url, path, start, end, original, threads, hide, clean):
    #创建当前目录
    mkdir(path)
    #删除未完成子目录
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
                
    #获取所有页面
    classPages=[]
    for page in range(start,end+1):
        classPages.append(urlroot+str(page))
    #print(classPages)  
    
    if classPages:
        #获取下级页面信息
        page = 1000+start-1
        for url_classpage in classPages:
            page += 1
            print('-'*10+url_classpage)
            items = [url_classpage]
            if items:
                for item in items:
                    url_firstpage = item
                    t = getTitle(url_firstpage)
                    if t == None:
                        continue
                    #t = urllib.request.unquote(t) #避免重复，用url最末段当目录名
                    title_firstpage = str(page)+' '+validateTitle(t)

                    classpath = path
                    #print(classpath)
                    #assert()
                    if mkdir(classpath+os.sep+title_firstpage):
                        Error = False
                        mkdir(classpath+os.sep+title_firstpage+os.sep+'UNFINISHED')
                        #print(url_firstpage)
                        singlePages = [url_firstpage]
                        if singlePages:
                            i = 1000 #图片名称                           
                            urlQueue = queue.Queue()
                            for url_singlepage in singlePages:
                                #time.sleep(0.5)
                                #print('-'*30+url_singlepage)
                                imgs = getImg(url_singlepage)
                                if imgs:
                                    for img in imgs:
                                        i = i+1
                                        name_tail = img.split('.')[-1]
                                        if original:
                                            img_root = os.path.split(img)[0]
                                            img_name = os.path.split(img)[1]
                                            if 'thumb' in img_name and 'x' in img_name:
                                                img = img_root+'/'+img_name[6:-12]+'.'+name_tail
                                            #print(img)                                        
                                        name_jpg = str(i)+'.'+name_tail
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
                            rmdir(classpath+os.sep+title_firstpage+os.sep+'UNFINISHED')
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


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=1)
    parser.add_argument("--original", type=int, default=0)
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--hide", type=int, default=1)
    parser.add_argument("--clean", type=int, default=0)
    args = parser.parse_args()
    return args
    
    
###### Main ######
if __name__ == "__main__":
    args = get_args()
    URLROOT = 'https://ygugu4.com/bbs/board.php?bo_table=pic&wr_id='


    URLCRAWLER = URLROOT+'/'
    START = args.start
    END = args.end
    ORIGINAL = args.original
    THREADS = args.threads
    HIDE = args.hide
    CLEAN = args.clean
    if ORIGINAL:
        PATH = 'F:/2017/TMP/Download_MM_D'
    else:
        PATH = 'F:/2017/TMP/Download_MM_C'
    crawler(URLROOT, URLCRAWLER, PATH, START, END, ORIGINAL, THREADS, HIDE, CLEAN)

