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

HEADER={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.137 Safari/537.36 LBBROWSER'}  
#PROXIE = {'http':'http://221.0.232.13:61202','https':'https://211.86.50.105:61202'}
TIMEOUT = 1



#传入图片地址，文件名，保存单张图片
def saveImg(imageURL,fileName,timeSet=0):
    if timeSet == 0:
        timeSet = TIMEOUT
    try: 
        r = urllib.request.Request(imageURL, headers=HEADER)
        u = urllib.request.urlopen(r, timeout=timeSet)
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
        timeset = 1
        while saveImg(url, filename, timeset) == False and retry>0:
            time.sleep(1.1)
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
        print('==== UNKNOWN ====    '+content)
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
        print('==== UNKNOWN ====    '+content)
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

#获取页面信息
def getPage(url, num):
    #简单的把原始url最后的'.html'这5位截掉，拼上页号和html后缀
    urlPage = url[:-5] + '-page-' + str(num) + '.html' 
    #print(urlPage)
    try:
        #获取当前页面所有主题
        request = urllib.request.Request(urlPage, headers=HEADER)
        response = urllib.request.urlopen(request).read().decode('utf-8')
        #print(response)
        
        #剥离其它部分，仅保留相关列表
        pattern = re.compile('<ul class="textList">(.*?)</ul>', re.S)
        content = re.search(pattern, response).group(0)
        #print(content)

        #逐个提取主题
        pattern = re.compile('<li><a href="(.*?)" target="_blank"><span>(.*?)</span>(.*?)</a></li>', re.S)
        items = re.findall(pattern, content)#item[0]本地页面地址，需加上urlroot这个网站地址前缀，item[1]发布日期，item[2]标题
        #for item in items:
        #    print(item[0], item[1], item[2])
        return items
    except urllib.error.URLError as e:
        print('==== TIMEOUT ====    '+urlPage)
        print(e.reason)
        return None
    except Exception as e:
        print('==== UNKNOWN ====    '+urlPage)
        print(e)
        return None

#获取当前页图片信息并保存
def getImg(url, gif):
    try: 
        request = urllib.request.Request(url, headers=HEADER)
        response = urllib.request.urlopen(request, timeout=TIMEOUT).read().decode('utf-8')
        response = re.sub(r'\xa0', r" ", response)
        #print(response)
    
        pattern = re.compile('<div class="picContent">(.*?)</div>', re.S)
        content = re.search(pattern, response).group(0)
        #print(content)
    
        content = re.sub('<br>|<br.*?/>', '\n', content)
        if gif:
            pattern = re.compile('(?i)<img.*?src="(http.*?gif)".*?>')
        else:
            pattern = re.compile('(?i)<img.*?src="(http.*?jpg|http.*?png|http.*?jpeg)".*?>')
        items = re.findall(pattern, content)#item图片地址，绝对地址
        #print(items)
        #for item in items:
        #    print(item)
        return items
    except urllib.error.URLError as e:
        print('==== TIMEoUT ====    '+url)
        print(e.reason)
        return None
    except Exception as e:
        print('==== UNKNOWN ====    '+url)
        print(e)
        return None
            
            
#获取当前页图片信息并保存
def getMagnet(url):
    try: 
        request = urllib.request.Request(url, headers=HEADER)
        response = urllib.request.urlopen(request, timeout=TIMEOUT).read().decode('utf-8')
        response = re.sub(r'\xa0', r' ', response)
        #print(response)

        pattern = re.compile('<div class="picContent">(.*?)</div>', re.S)
        content = re.search(pattern, response).group(0)
        #print(content)
    
        pattern = re.compile('magnet:.*[^<]')
        content = re.search(pattern, content)
        if content:
            content = content.group(0)
            content = re.sub(r'[\s]', r'', content)
            content = re.sub(r'<span>|</span>|</b>|<br/>', r'', content)
            #print(content)   
            return content
        else:
            return None
    except urllib.error.URLError as e:
        print('==== TIMEoUT ====    '+url)
        print(e.reason)
        return None
    except Exception as e:
        print('==== UNKNOWN ====    '+url)
        print(e)        
        return None
            
            
#爬虫入口
def crawler(urlroot, url, start, end, path, magnet, gif, content, threads, hide, clean, ignore):
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
                        if hide == 0:
                            try:
                                print('==== DELETE ====    '+dirc)
                            except Exception as e:
                                print('==== DELETE ====')
        else:
            print("dir not exists")    
    
    SLEEP_CNT = 10 #重试次数
    SLEEP_LNG = 120 #秒
    #遍历指定页面
    assert(start >= 1 and start <= end)
    for i in range(start-1, end):
        print('-'*10+"==== PAGE ", i+1, " ===="+'-'*40)
        saveFlag(str(i+1)+' ', path+os.sep+'FLAG.txt')
        #对每一页，重试若干次并加入间隔，避免IP被ban
        retry = SLEEP_CNT
        while retry > 0:
            items = getPage(url, i+1) #i start from 0
            if items:
                retry = 0
                #遍历当前页面每一个内容链接，下载当前链接图片
                for item in items:
                    #通过‘content’筛选标题，只下载指定的页面的内容, 必须用""包裹标题指定内容!!
                    if content.upper() not in item[2].upper():
                        continue
                    urlId = urlroot+item[0]
                    folder = item[1]+' '+item[2]
                    folder = validateTitle(folder)
                    name = validateTitle(item[2])
                    #打印当前要下载的链接信息
                    if hide == 1:
                        print('-'*20+urlId)
                    else:
                        try:
                            print('-'*20+urlId, folder)
                        except:
                            print('-'*20+urlId)
                    if mkdir(path+'./'+folder):
                        Error = False
                        imgs = getImg(urlId, gif)
                        if imgs == None:    #add a retry
                            imgs = getImg(urlId, gif)
                        if (imgs):
                            mkdir(path+os.sep+folder+os.sep+'UNFINISHED')#标记未完成
                            #下载图片
                            i = 1000
                            #多线程处理， 线程数即参数
                            if threads > 0:
                                urlQueue = queue.Queue()
                                for img in imgs:
                                    i=i+1
                                    if gif:
                                        jpgname = str(i)+'.gif'
                                    else:
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
                            time.sleep(2.1) #DELAY
                            rmdir(path+os.sep+folder+os.sep+'UNFINISHED')#标记已完成
                        else:
                            Error = True
                            if hide == 1:
                                print('==== ERROR ====    '+urlId)
                            else:
                                try: 
                                    print('==== ERROR ====    '+folder)
                                except:
                                    print('==== ERROR ====    '+urlId)
                                    
                        #下载种子
                        if magnet == 1 and Error == False:
                            seed = getMagnet(urlId)
                            if (seed):
                                mkdir(path+os.sep+folder+'./UNFINISHED')#标记未完成
                                print(seed)
                                if saveMagnet(seed, path+os.sep+folder+os.sep+name+'.txt') == False:
                                    Error = True
                                #saveMagnet(seed, path+os.sep+folder+os.sep+folder+'.txt')
                                time.sleep(2.1) #DELAY
                                rmdir(path+os.sep+folder+os.sep+'UNFINISHED')#标记已完成
                            else:
                                Error = True
                                if hide == 1:
                                    print('==== ERROR ====    '+urlId)
                                else:
                                    try: 
                                        print('==== ERROR ====    '+folder)
                                    except:
                                        print('==== ERROR ====    '+urlId)                                    
                        if Error == True:
                            if ignore == 1:
                                mkdir(path+os.sep+folder+os.sep+'ERROR')#标记出错但主动忽略
                                if hide == 1:
                                    print('==== IGNORE ====    '+urlId)
                                else:
                                    try:
                                        print('==== IGNORE ====    '+folder)
                                    except:
                                        print('==== IGNORE ====    '+urlId)
                            else:
                                rmdir(path+os.sep+folder)
                                if hide == 1:
                                    print('==== REMOVE ====    '+urlId)
                                else:
                                    try:
                                        print('==== REMOVE ====    '+folder)
                                    except:
                                        print('==== REMOVE ====    '+urlId)
                    else:
                        if hide == 1:
                            print('==== EXIST ====    '+urlId)    
                        else:
                            try:
                                print('==== EXIST ====    '+folder)   
                            except:
                                print('==== EXIST ====    '+urlId)  
            else:
                retry = retry-1
                print("==== SLEEP ", retry, " ====")
                time.sleep(SLEEP_LNG)
        time.sleep(6) #每页休息一下

        
def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", type=int, default=9)
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=1)
    parser.add_argument("--magnet", type=int, default=0)
    parser.add_argument("--gif", type=int, default=0)
    parser.add_argument("--content", type=str, default="")
    parser.add_argument("--threads", type=int, default=0)
    parser.add_argument("--hide", type=int, default=1)
    parser.add_argument("--clean", type=int, default=0)
    parser.add_argument("--ignore", type=int, default=0)
    args = parser.parse_args()
    return args
    
###### Main ######
if __name__ == "__main__":
    args = get_args()
    URLROOT = 'http://www.77eep.com'
    URLCRAWLER = 'http://www.77eep.com/article-list-id-'+str(args.index)+'.html'
    PATH = 'F:/2017/TMP/Download_EPP_'+str(args.index)
    START = args.start
    END = args.end
    MAGNET = args.magnet
    GIF = args.gif
    CONTENT = args.content
    THREADS = args.threads
    HIDE = args.hide
    CLEAN = args.clean
    IGNORE = args.ignore
    crawler(URLROOT, URLCRAWLER, START, END, PATH, MAGNET, GIF, CONTENT, THREADS, HIDE, CLEAN, IGNORE)

#没保存完的目录，放一张名为unfinished的图片，图片内容也是这个，便于预览查找