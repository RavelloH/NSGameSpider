# Nintendo Switch游戏封面爬取
# Verson:1.2.0
# Author:RavelloH
# LICENSE:MIT
# 爬取内容归Nintendo及相关工作室所有

from urllib.request import urlopen
from bs4 import BeautifulSoup as bs
from wget import download
import os    
os.makedirs('./img/',exist_ok=True)
# 设置目标路径
link = "store.nintendo.com.hk/games/recently-released"
# 爬取
html = urlopen("https://"+link)
# 解析
obj = bs(html.read(),'html.parser')
pic_info = obj.find_all('img',class_="product-image-photo mplazyload mplazyload-transparent")  
print(pic_info)
try:
    
    for i in pic_info:
        pic = str(i['data-src'])
        name = str(i['alt'])
        if "http" not in pic:
            if "data" in pic:
                continue
            else:
                if "//" in pic:
                    links = "http:"+pic
                else:
                    if pic[0] == "/":
                        links = "http://"+link+pic
                    else:
                        links = "http://"+link+"/"+pic
            
        else:
            links = pic    
        # 下载
        print(links+"\n"+name)
        download(links,out='./img/'+name+'.jpg')
except:
    pass
for file_name in os.listdir('./img/'):
    if '(1)' in file_name:
        os.remove('./img/' + file_name)
