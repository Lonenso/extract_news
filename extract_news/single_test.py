from newspaper import Article, Config
from .patcher import Patcher
import requests
config = Config()
config.language = 'zh'
config.fetch_images = False
p = Patcher()
p.enable_patch()
article = Article(url="http://www.ifeng.com/", config=config)
article.download()
# http://news.sina.com.cn/zl/zatan/2015-03-17/09153392.shtml
r = requests.get(url="http://news.sina.com.cn/zl/zatan/blog/2015-03-21/09043418/1187989361/46cf47710102vhrl.shtml")
#
# print(r.content)
# article.download(r.content, input_url=r.url)
article.parse()
print(article.text)