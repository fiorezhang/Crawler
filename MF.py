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
TIMEOUT = 5



#´«ÈëÍ¼Æ¬µØÖ·£¬ÎÄ¼þÃû£¬±£´æµ¥ÕÅÍ¼Æ¬
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

#¶àÏß³Ì»ñÈ¡Í¼Æ¬        
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
            #print(e) #µ±queue¿ÕÊ±£¬ÕâÀï»á´òÓ¡Ò»ÐÐ¿ÕÄÚÈÝ
            break
        #print("-------- -------- Current Thread: "+threading.currentThread().name+", file: "+filename)
        if saveImg(url, filename) == False: #ÖØ¸´¼¸´Î³¢ÊÔÏÂÔØ£¬¼ä¸ôÒ»¶ÎÊ±¼ä£¬Ö»Ó°Ïìµ±Ç°Ïß³Ì
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
            return self.result  # Èç¹û×ÓÏß³Ì²»Ê¹ÓÃjoin·½·¨£¬´Ë´¦¿ÉÄÜ»á±¨Ã»ÓÐself.resultµÄ´íÎó
        except Exception:
            return None


#±£´æÎÄ¼þÊ±ºò, È¥³ýÃû×ÖÖÐµÄ·Ç·¨×Ö·û
def validateTitle(title):
    rstr = r"[\/\\\:\*\?\"\<\>\|]"  # '/ \ : * ? " < > |'
#    rstr = r"[\*\?\"\<\>\|]"  # '/ \ : * ? " < > |'
    new_title = re.sub(rstr, r"_", title)  # Ìæ»»ÎªÏÂ»®Ïß
    return new_title
     
#´´½¨ÐÂÄ¿Â¼
def mkdir(path):
    path = path.strip()
    # ÅÐ¶ÏÂ·¾¶ÊÇ·ñ´æÔÚ
    # ´æÔÚ     True
    # ²»´æÔÚ   False
    isExists=os.path.exists(path)
    #print(isExists)
    # ÅÐ¶Ï½á¹û
    if not isExists:
        # Èç¹û²»´æÔÚÔò´´½¨Ä¿Â¼
        # ´´½¨Ä¿Â¼²Ù×÷º¯Êý
        os.makedirs(path)
        return True
    else:
        # Èç¹ûÄ¿Â¼´æÔÚÔò²»´´½¨£¬²¢ÌáÊ¾Ä¿Â¼ÒÑ´æÔÚ
        return False     

#É¾³ýÄ¿Â¼
def rmdir(path):
    shutil.rmtree(path)
       

#»ñÈ¡Ò³ÃæÐÅÏ¢
def getPage(urlPage):
    try:
        #print(urlPage)
        #»ñÈ¡µ±Ç°Ò³ÃæËùÓÐÖ÷Ìâ
        request = urllib.request.Request(urlPage, headers=HEADER)
        response = urllib.request.urlopen(request).read().decode('gbk','ignore')
        #print(response)
        
        #°þÀëÆäËü²¿·Ö£¬½ö±£ÁôÏà¹ØÁÐ±í
        pattern = re.compile('<article class="article">(.*?)</article>', re.S)
        content = re.search(pattern, response).group(1)
        #print(content)
        
        #Öð¸öÌáÈ¡Ö÷Ìâ
        # <a href="http://www.adult-comix.net/beach-adventure-4/milftoon" title="Beach Adventure 4" rel="bookmark">Beach Adventure 4</a>
        pattern = re.compile('<h2 class="title">.*?<a href="(.*?)" title="(.*?)".*?</a>', re.S)
        items = re.findall(pattern, content)#item[0]±¾µØÒ³ÃæµØÖ·£¬Ðè¼ÓÉÏurlrootÕâ¸öÍøÕ¾µØÖ·Ç°×º£¬item[1]±êÌâ
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

def getAllImg(url):
    ret = True
    img_list = []
    
    while True:
        try:
            #»ñÈ¡µ±Ç°Ò³ÃæËùÓÐÖ÷Ìâ
            request = urllib.request.Request(url, headers=HEADER)
            response = urllib.request.urlopen(request).read().decode('gbk','ignore')
            #print(response)

            #»ñÈ¡µ±Ç°Ò³Í¼Æ¬¡ª¡ª¾ÍÒ»ÕÅ
            pattern = re.compile('<div id="ngg-image-0".*?>(.*?)</div', re.S)
            content = re.search(pattern, response).group(1)
            #print(content)
            
            pattern = re.compile("(?i)<img.*?src='(http.*?jpg)'.*?>", re.S)
            img = re.search(pattern, content).group(1)
            if len(img_list)==0 or img != img_list[0]:
                img_list.append(img)
                #print(img_list)
            else:
                #print("REPEAT")
                break
            #print(img)            
            
            #»ñÈ¡ÏÂÒ»Ò³µØÖ·£¬Ð´ÈëURL¹©Ñ­»·
            pattern = re.compile("<div class='next'>(.*?)</div", re.S)
            content = re.search(pattern, response).group(1)
            #print(content)
            
            pattern = re.compile("(?i)<a class.*?href='(.*?)'.*?</a>", re.S)
            url = re.search(pattern, content).group(1)
            print(url)
            
            time.sleep(0.2)
        except urllib.error.URLError as e:
            print(e.reason)
            ret = False
            break
        except Exception as e:
            print(e)
            ret = False
            break
    #assert()
    if ret:
        return img_list
    else:
        return None
            

#ÅÀ³æÈë¿Ú
def crawler(urlroot, url, path, threads, hide, clean):
    #´´½¨µ±Ç°·ÖÀàµÄÄ¿Â¼
    mkdir(path)
    #É¾³ýÎ´Íê³ÉÄ¿Â¼
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
                
    #»ñÈ¡µ±Ç°·ÖÀàÏÂËùÓÐÒ³ÃæURL
    print(url)

    for i_page in range(17):
        url_classpage = url+str(i_page+1)
        print('-'*10+url_classpage)
        items = getPage(url_classpage)
        if items:
            for item in items:
                time.sleep(0.2)
                url_firstpage = item[0]
                title_firstpage = validateTitle(item[1])
                if hide == 0:
                    print('-'*20+url_firstpage+'-'*10+title_firstpage)
                else:
                    print('-'*20+url_firstpage)

                classpath = path
                #print(classpath)
                #assert()
                if mkdir(classpath+os.sep+title_firstpage):
                    Error = False
                    mkdir(classpath+os.sep+title_firstpage+os.sep+'UNFINISHED')#±ê¼ÇÎ´Íê³É
                      
                    i = 1000 #ÓÃ×÷Í¼Æ¬ÎÄ¼þÃû
                    urlQueue = queue.Queue()
                    imgs = getAllImg(url_firstpage)
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
                    rmdir(classpath+os.sep+title_firstpage+os.sep+'UNFINISHED')#±ê¼ÇÒÑÍê³É
                    if Error:
                        print('REMOVE')
                        rmdir(classpath+os.sep+title_firstpage)
                else:
                    print('EXIST')

        
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
    URLROOT = 'http://www.adult-comix.net'
    PATH = 'F:/2017/TMP/Download_MILF'
    URLCRAWLER = URLROOT+'/page/'
    THREADS = args.threads
    HIDE = args.hide
    CLEAN = args.clean
    crawler(URLROOT, URLCRAWLER, PATH, THREADS, HIDE, CLEAN)

#Ã»±£´æÍêµÄÄ¿Â¼£¬·ÅÒ»ÕÅÃûÎªunfinishedµÄÍ¼Æ¬£¬Í¼Æ¬ÄÚÈÝÒ²ÊÇÕâ¸ö£¬±ãÓÚÔ¤ÀÀ²éÕÒ

