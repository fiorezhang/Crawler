# -*- coding: utf-8 -*-
import time
import re
import urllib.request  
from selenium import webdriver
from selenium.common.exceptions import TimeoutException

print(str(time.time()))

#利用PhantomJS加载网页
browser = webdriver.PhantomJS(executable_path=r'C:\Users\FioreZ\.anaconda\phantomjs-2.1.1-windows\bin\phantomjs.exe')
browser.set_page_load_timeout(30) # 最大等待时间
#当加载时间超过30秒后，自动停止加载该页面


for i in range(22):
    timeout = 1
    while True:    
        try:
            print('-'*20+str(i+1))
            print(str(time.time()))
            browser.set_page_load_timeout(timeout)
            browser.get(r'https://www.8muses.com/comics/picture/MilfToon-Comics/Lemonade/Lemonade-1/'+str(i+1))
        except TimeoutException:
            browser.execute_script('window.stop()')
        source = browser.page_source #获取网页源代码
        #print(source)
        
        pattern = re.compile('<div class="photo"(.*?)</div>')
        contents = re.search(pattern, source)
        if contents != None:
            content = contents.group(1)
            print(content)
        else:
            timeout *= 2
            continue

        pattern = re.compile('<img src="(.*?jpg)"')
        contents = re.search(pattern, content)
        if contents != None:
            content = contents.group(1)
            print(content)
            break

    print("BROWSER: ", browser)
    browser = webdriver.PhantomJS(executable_path=r'C:\Users\FioreZ\.anaconda\phantomjs-2.1.1-windows\bin\phantomjs.exe')
    print("BROWSER: ", browser)

    
browser.quit()
