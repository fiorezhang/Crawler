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
import sys

HEADER={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.137 Safari/537.36 LBBROWSER'}  
#PROXIE = {'http':'http://221.0.232.13:61202','https':'https://211.86.50.105:61202'}
TIMEOUT = 20

URLROOT = 'http://www.73wxw.com'
PATH = 'F:/2017/TMP/Download_WXW'
SESSION_MAX = 600

def saveContent(content, fileName):
    with open(fileName, "a+") as f:
        f.write(content)
        f.close()

class Logger(object):
    def __init__(self, filename="Default.log"):
        self.terminal = sys.stdout
        self.log = open(filename, "a")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        pass

#多线程获取图片        
def fetchTxt(imageURLQueue):
    while True:
        ret = True        
        try:
            urlpair = imageURLQueue.get_nowait()
            i = imageURLQueue.qsize()
            #print("Queue Size "+str(i))
            url = urlpair[0]
            filename = urlpair[1]
        except Exception as e:
            #print(e) #当queue空时，这里会打印一行空内容
            break
        print("-------- -------- Current Thread: "+threading.currentThread().name+", file: "+filename)
        print(' '*10+url+' '+filename)
        if os.path.exists(filename):
            print(' '*20+filename+' EXIST')
            continue
        sessions = getAllSessions(url)
        if len(sessions) > SESSION_MAX:
            print(' '*20+filename+' OVERWEIGHT')
            continue
        if sessions:
            for session in sessions:
                #print(session)
                url_s = URLROOT+'/'+session[0]
                name_s = session[1]
                print(' '*20+url_s+' '+filename+'>>>'+name_s)
                title = "\r\n"*4+"#"*10+name_s+"#"*10+"\r\n"*2
                retry = 3
                while retry > 0:
                    retry -= 1
                    content = getContent(url_s)
                    if content != None:
                        break     
                    else:
                        time.sleep(1)
                if content != None:
                    saveContent(title, filename+'.bak') #没有下载完成的暂时标记bak，完成后会改回txt
                    saveContent(content, filename+'.bak')
                else:
                    print(' '*20+'ERROR '+url_s+' '+filename+'>>>'+name_s)
                    ret = False
                    break
            if ret == True:        
                os.rename(filename+'.bak', filename)
    print("-------- -------- End Thread: "+threading.currentThread().name+" with: ", ret)
    return
           

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

def getAllPages(url):
    try:
        #获取当前页面所有主题
        request = urllib.request.Request(url, headers=HEADER)
        response = urllib.request.urlopen(request).read().decode('gbk', 'ignore')
        #response = urllib.request.urlopen(request, timeout=TIMEOUT).read().decode('gbk')
        #print(response)
        
        #剥离其它部分，仅保留相关列表
        pattern = re.compile('<div id="main">(.*?)<div class="footer">', re.S)
        content = re.search(pattern, response).group(0)
        #print(content)
        
        #<li><a href="/33/33333/">大唐群芳谱</a>/霁月飘雪</li>
        #pattern = re.compile('<li><a href="(.*?)">(.*?)</a>/(.*?)</li>', re.S)
        pattern = re.compile('<a href="(.*?)">(.*?)</a>', re.S)
        items = re.findall(pattern, content)
        
        #for i, item in enumerate(items):
        #    print(item)

        return items
    except urllib.error.URLError as e:
        print(e.reason)
        return None
    except Exception as e:
        print(e)
        return None

def getAllSessions(url):
    try:
        #获取当前页面所有主题
        request = urllib.request.Request(url, headers=HEADER)
        response = urllib.request.urlopen(request).read().decode('gbk', 'ignore')
        #response = urllib.request.urlopen(request, timeout=TIMEOUT).read().decode('gbk')
        #print(response)
        
        #剥离其它部分，仅保留相关列表
        pattern = re.compile('<div id="list">(.*?)<div id="footer"', re.S)
        content = re.search(pattern, response).group(0)
        #print(content)
        
        #<li><a href="/33/33333/">大唐群芳谱</a>/霁月飘雪</li>
        #pattern = re.compile('<li><a href="(.*?)">(.*?)</a>/(.*?)</li>', re.S)
        pattern = re.compile('<a href="(.*?)".*?>(.*?)</a>', re.S)
        items = re.findall(pattern, content)
        
        #for i, item in enumerate(items):
        #    print(item)

        return items   
    except urllib.error.URLError as e:
        print(e.reason)
        return None
    except Exception as e:
        print(e)
        return None        

def getContent(url):
    try:
        #获取当前页面所有主题
        request = urllib.request.Request(url, headers=HEADER)
        response = urllib.request.urlopen(request).read().decode('gbk', 'ignore')
        #response = urllib.request.urlopen(request, timeout=TIMEOUT).read().decode('gbk')
        #print(response)
        
        '''
        #剥离其它部分，仅保留相关列表
        pattern = re.compile('<table class="border_l_r"(.*?)<div class="top_set"', re.S)
        content = re.search(pattern, response).group(0)
        print(content)
        '''
        
        #<li><a href="/33/33333/">大唐群芳谱</a>/霁月飘雪</li>
        #pattern = re.compile('<li><a href="(.*?)">(.*?)</a>/(.*?)</li>', re.S)
        pattern = re.compile('<p>(.*?)</p>', re.S)
        content = re.search(pattern, response).group(0)
        
        content = content.replace(r"&nbsp;", "").replace(r"<br />", "").replace(r"</p>", "")
        content = (content.replace(r"yīn", "阴")
                          .replace(r"yín", "淫")
                          .replace(r"jīng", "茎")
                          .replace(r"jī", "鸡")
                          .replace(r"ròu", "肉")
                          .replace(r"cāo", "操")
                          .replace(r"xiōng", "胸")
                          .replace(r"rǔ", "乳")
                          .replace(r"bī", "屄")
                          .replace(r"guī", "龟")
                          .replace(r"nǎi", "奶")
                          .replace(r"yáng", "阳")
                          .replace(r"xiāo", "小")
                          .replace(r"sāo", "骚")
                          .replace(r"aì", "爱")
                          .replace(r"nv", "女")
                          .replace(r"shè", "射")
                          .replace(r"yu", "欲")
                          )
        
        #print(content)
        return content   
    except urllib.error.URLError as e:
        print(e.reason)
        return None
    except Exception as e:
        print(e)
        return None        
        
                
        
        
#爬虫入口
def crawler(urlroot, url, path, threads): 
    timeCurrent = time.strftime("%H-%M-%S", time.localtime())
    sys.stdout = Logger("./wxw_"+timeCurrent+".log")
    print("LOG RELOCATED") # this is should be saved in yourlogfilename.txt

    #创建当前分类的目录
    mkdir(path)
    
    #删除未完成
    if os.path.exists(path):
        files = os.listdir(path)
        for file in files:
            if os.path.splitext(file)[1] == '.bak':
                print("REMOVE "+file)
                os.remove(path+os.sep+file)

    #获取当前分类下所有页面URL
    pages = getAllPages(url) 
    if pages:
        #获取当前分类所有页面的下级信息
        urlQueue = queue.Queue()
        for page in pages:
            url = URLROOT+'/'+page[0]
            name = validateTitle(page[1])
            #print('-'*10+url+' '+name)
            urlpair = [url, path+os.sep+name+'.txt']
            urlQueue.put(urlpair)
        startTime = time.time()
        ths = []
        for _ in range(0, threads):
            t = ImgThread(fetchTxt, args=(urlQueue,))
            ths.append(t)
        for t in ths:
            t.start()
        for t in ths:
            t.join()
#        for t in ths:
#            if t.get_result() == False: 
#                Error = True
#                print("ERROR "+name)
        endTime = time.time()
        

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--threads", type=int, default=1)
    args = parser.parse_args()
    return args
    
    
###### Main ######
if __name__ == "__main__":
    args = get_args()

    THREADS = args.threads
    URLCRAWLER = URLROOT+'/all/'

    crawler(URLROOT, URLCRAWLER, PATH, THREADS)
