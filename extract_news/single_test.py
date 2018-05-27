from newspaper import Article, Config
from extract_news.patcher import NewspaperPatcher
import requests
config = Config()
config.language = 'zh'
config.fetch_images = False
p = NewspaperPatcher()
p.enable_patch()
article = Article(url="http://mil.news.sina.com.cn/2018-05-18/doc-ihaturfs3429865.shtml", config=config)
article.download()
article.parse()
print(article.text)