## broadcrawler.py
采用Crawlspider,Rule 来提取链接,并利用自定义后的newspaper库来判断是否是新闻,解析网页内容,是新闻我们就解析,不是的话对于没对接的可以先扔掉
## Begin.py
可以直接运行,调试这个文件. 代替cmd启动,方便
## items.py
BroadcrawlerItem是存放新闻item的,similarity可以无视
## patcher.py
通过重写一些函数来实现自定义,写法如下:
1. 实现你要写的方法
2. 在enable_patch()中指定原类中方法的替换或者增加
3. 测试是否成功

```
    def enable_patch(self):
        Article.download = download
        Article.parse = parse
        Article.is_news = None
        Config.fetch_videos = None
        ContentExtractor.get_publishing_date = get_publishing_date
        ContentExtractor.get_authors = get_authors
        ContentExtractor.get_title = get_title
```
## pipeline.py
* JsonWithEncodingPipeline是以json保存
* MongoPipeline是以mongo保存
没有配置mongo的配置一下，网上教程很多
## settings.py
settings中相应设置字段我都有说明
## Reference
* Monkey patch
http://blog.hszofficial.site/TutorialForPython/%E5%85%83%E7%BC%96%E7%A8%8B/%E7%8C%B4%E5%AD%90%E8%A1%A5%E4%B8%81%E5%92%8C%E7%83%AD%E6%9B%B4%E6%96%B0.html

* Rule：
https://blog.csdn.net/wqh_jingsong/article/details/56865433

* difflib：
https://docs.python.org/3/library/difflib.html?highlight=difflib#module-difflib
