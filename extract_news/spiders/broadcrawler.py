import hashlib
from scrapy.spiders import CrawlSpider, Spider, Rule
from datetime import datetime
from selenium import webdriver
from scrapy import Request, FormRequest
import time
import requests
import json
from newspaper import Article, ArticleException, Config
from extract_news.items import BroadcrawlerItem
from scrapy.linkextractors import LinkExtractor
config = Config()
config.language = 'zh'
config.fetch_images = False
deny_regex = 'slide|blog|auto|weibo|baby|vip|book|picture|photo|video|tags|comment'


# global notitle, nodate, noauthor, notext = 0, 0, 0, 0
# global total
# global error
# class peopleSpider(Spider):
#     name = "peoplespider"
#     # allowed_domains = ['']
#     """
#     人民网的滚动新闻是一次性请求得到的，之后通过触发js事件加载到页面中
#     """
#     # start_urls = ['http://news.people.com.cn/', '']
#     # people_format = "{}.people.com.cn/{}/yy/mmdd/{}.html"
#     def start_requests(self):
#         timestamp = int(time.time()*1000)
#         people_url = "http://news.people.com.cn/210801/211150/index.js?_={}".format(timestamp)
#         yield Request(url=people_url, callback=self.parse)
#
#
#     def parse(self, response):
#         # with open("last.json", 'r') as f:
#         #     lastdata = json.load(f)
#         rawdata = json.loads(response.text)
#
#
#         def duplicate(seq, idfun=None):
#             # order preserving
#             if idfun is None:
#                 def idfun(x): return x
#             seen = {}
#             result = []
#             for item in seq:
#                 marker = idfun(item['id'])
#                 if marker in seen: continue
#                 seen[marker] = 1
#                 result.append(item)
#             return result
#
#         data = duplicate(rawdata['items'])
#         with open('{}.json'.format("last"), 'w') as f:
#             cleandata = {'items': data}
#             json.dump(cleandata, f)
#
#         for span in data:
#             url = span['url']
#             title = span['title']
#             date = span['date']
#             id = span['id']
#             item = BroadcrawlerItem()
#             try:
#                 article = Article(url=url, language='zh')
#                 article.download()
#                 article.parse()
#             except ArticleException as e:
#                 print("Status Error: ", e)
#             if title != article.title:
#                 print("{0}|*|{1}".format(title, article.title))
#             item['title'] = title
#             item['url'] = url
#             item['pubtime'] = date
#             item['content'] = article.text
#             yield item


# class peopleSpider(CrawlSpider):
#     name = 'peoplespider'
#     allowed_domains = ['politics.people.com.cn', 'world.people.com.cn', 'society.people.com.cn', 'www.people.com.cn']
#     start_urls = ['http://www.people.com.cn/']
#     # 这里可以通过rules来获取当天的新闻， 我想爬取某一天的新闻可能比较悬
#     rules = (
#         Rule(LinkExtractor(allow=('index\d+.html',)), follow=True),
#         Rule(LinkExtractor(allow=('.*/\d{4}/\d{4}/.*\.html$',), deny=('GB')), follow=True, callback='parse_news')
#     )
#
#     def parse_news(self, response):
#         item = BroadcrawlerItem()
#         article = Article(url=response.url, language='zh')
#         article.download()
#         article.parse()
#         item['title'] = article.title
#         item['pubtime'] = article.publish_date.strftime("%Y-%m-%d")
#         item['content'] = article.text
#         item['url'] = response.url
#         yield item
#
#
# class sohuSpider(CrawlSpider):
#     name = 'sohuspider'
#     start_urls = ["http://news.sohu.com/"]
#     allowed_domains = ['www.sohu.com']
#     rules = (
#         Rule(LinkExtractor(allow=('',)), follow=True),
#         Rule(LinkExtractor(allow=('a/',)), follow=True, callback='parse_news'),
#     )
#
#     def parse_news(self, response):
#         item = BroadcrawlerItem()
#         try:
#             article = Article(url='', language='zh')
#             article.download(input_html=response.content)
#             article.parse()
#         except ArticleException:
#             pass
#         item['title'] = article.title
#         if isinstance(article.publish_date, datetime):
#             item['pubtime'] = article.publish_date.strftime("%Y-%m-%d %H:%M:%S")
#         else:
#             item['pubtime'] = "N/A"
#         item['content'] = article.text
#         item['url'] = response.url
#         item['author'] = article.authors
#         yield item
# class ifengSpider(CrawlSpider):
#     """
#     初步来看凤凰网似乎不适合用rule这种机制来爬取全站，存在很多的js动态加载
#     但凤凰网的滚动新闻，新闻列表自己整合在了一起，我想通过这个入口使用rule这种机制也不错
#     之所以不具体地分析是因为懒得弄
#     再者，凤凰网跟人民网的爬取起来的差别是 我能够很方便的限制日期且能够得到数据，而人民网两部分来谈：滚动部分包括将近一个月的新闻
#     且没有日期可以限定，全站爬取部分无法肯定能够爬取完整，今天我还认识到，某一些常驻在主页上的不一定是当天新闻，是一些近期热点
#     """
#     name = 'ifengspider'
#     allowed_domains = ['news.ifeng.com']
#     start_urls = ['http://www.ifeng.com/']
#     # rules = (
#     #     Rule(LinkExtractor(allow=('.*rtlist.shtml',)), follow=True),
#     #     Rule(LinkExtractor(allow=('.*/\d{8}/.*.shtml',)), follow=True, callback='parse_news')
#     # )
#     rules = (
#         Rule(LinkExtractor(allow=(''), deny=(deny_regex)), follow=True, callback='parse_news'),
#     )
#
#     def parse_news(self, response):
#         item = BroadcrawlerItem()
#         try:
#             article = Article(url='', config=config)
#             article.download(input_html=response)
#             article.parse()
#         except ArticleException:
#             pass
#         if article.is_news:
#             item['title'] = article.title
#             if isinstance(article.publish_date, datetime):
#                 item['pubtime'] = article.publish_date.strftime("%Y-%m-%d %H:%M:%S")
#             else:
#                 item['pubtime'] = "N/A"
#             item['content'] = article.text
#             item['url'] = response.url
#             item['author'] = article.authors
#             yield item
#         else:
#             print("|||||||"+response.url)
#

class sinaSpider(CrawlSpider):
    name = 'sinanews'
    start_urls = ["http://news.sina.com.cn/"]
    allowed_domains = ['sina.com.cn']
    # base_url = 'http://roll.news.sina.com.cn/s/channel.php?ch=01#col=90,91,92&spec=&type=&ch=01&k=&offset_page=0&offset_num=0&num=80&asc=&page={0}'

    rules = (
        Rule(LinkExtractor(allow=(), deny=(deny_regex,)), follow=False, callback='parse_news'),
    )
    # '.*\d{4}-\d{2}-\d{2}/doc.*shtml',

    # def start_requests(self):
    #     def get_max():
    #         browser = webdriver.Chrome("D:\Chrome\chromedriver.exe")
    #         browser.get(self.base_url.format(1))
    #         time.sleep(5)
    #         p = browser.find_element_by_xpath('//*[@id="d_list"]/div/span[14]/a')
    #         rearend = int(p.text)
    #         browser.quit()
    #         return rearend
    #     max = get_max()
    #     urls = []
    #     for i in range(1, max + 1):
    #         url = self.base_url.format(i)
    #         urls.append(url)
    #     for i in urls:
    #         yield self.make_requests_from_url(i)

    def parse_news(self, response):
        item = BroadcrawlerItem()
        article = Article(url='', config=config)
        article.download(input_html=response)
        article.parse()

        if article.is_news:
            item['title'] = article.title
            if isinstance(article.publish_date, datetime):
                item['pubtime'] = article.publish_date.strftime("%Y-%m-%d %H:%M:%S")
            else:
                item['pubtime'] = "N/A"
            item['content'] = article.text
            item['url'] = response.url
            item['author'] = article.authors
            item['_id'] = hashlib.md5(response.url.encode('utf-8')).hexdigest()
            yield item
        else:
           # self.start_urls.append(response.url)
            pass


"""
目前完成 
稳定提取时间，
限制域名 需设计算法

"""


#TODO:pipeline item 过滤
#TODO:  限制域名   a.b.c.d.e   b.c.d.e
#TODO： newspaper的cleaner运行流程
#TODO: 如何加速
#TODO: 健壮性
#TODO: 时间控制
#TODO: 过滤网页
