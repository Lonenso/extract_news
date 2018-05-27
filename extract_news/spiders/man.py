import hashlib
import re
from datetime import datetime

import logging
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from extract_news.items import SimilarityItem
from newspaper import Article, Config
import difflib

config = Config()
config.language = 'zh'
config.fetch_images = False
logger = logging.getLogger(__name__)

SINA = r'.*\d{4}-\d{2}-\d{2}/doc.*shtml'
IFENG = r'.*/\d{8}/.*.shtml'
TENCENT = r'\.html?'
PEOPLE = r'.*/\d{4}/\d{4}/.*\.html$'
SOHU = r'\/a\/'
HUANQIU = r'\d{4}-\d{2}.*.html?'

allow_regex = SINA + "|" + IFENG + "|" +TENCENT + "|" + PEOPLE + "|" + SOHU + "|" + HUANQIU
class manSpider(CrawlSpider):
    name = "manspider"
    start_urls = ["http://news.sina.com.cn/",
                  "http://news.ifeng.com/",
                  "http://news.qq.com/",
                  "http://www.people.com.cn/",
                  "http://news.sohu.com/",
                  "http://www.huanqiu.com/",]
    allowed_domains = ['sina.com.cn',
                       'ifeng.com',
                       'news.qq.com',
                       'people.com.cn',
                       'sohu.com',
                       'huanqiu.com']
    rules = (
        Rule(LinkExtractor(allow=()), follow=True, callback='parse_news'),
    )

    def parse_news(self, response):
        item = SimilarityItem()
        article = Article(url='', config=config)
        article.download(input_html=response)
        article.parse()
        if article.is_news:
            if article.title and article.title != '':
                item['title'] = article.title
                item['ltitle'] = len(article.title)
            else:
                item['title'] = "N/A"
                item['ltitle'] = "N/A"
            if article.h1 and article.h1 != '':
                item['h1'] = article.h1
            else:
                item['h1'] = "N/A"
            if isinstance(article.publish_date, datetime):
                item['pubtime'] = article.publish_date.strftime("%Y-%m-%d %H:%M:%S")
            else:
                item['pubtime'] = "N/A"
            if article.text and article.text!='':
                item['content'] = article.text
                item['lcontent'] = len(article.text)
            else:
                item['content'] = "N/A"
                item['lcontent'] = "N/A"
            item['url'] = response.url

            def foo(a, b):
                if a and b:
                    return difflib.SequenceMatcher(None, a, b).quick_ratio()
                else:
                    logger.error("a:{0} b:{1}".format(a,b))
            item['h1_title_siml'] = foo(article.h1, article.title)
            item['title_content_siml'] =foo(article.title, article.text)
            item['_id'] = hashlib.md5(response.url.encode('utf-8')).hexdigest()
            yield item
        else:
            pass
            # 改成bfo后 第一次运行 2018/5/15 19:52
            # 第二次运行 00:42 到早上 8点左右 30421个item 吃满内存
            # 调整 log_level 为 info 禁止重定向
            # 控制页面时间 设置log_file

            # def get_host_regex(url):
            #     regex = r'(?<=://)((?:[\w-]+\.)+[\w-]+)'
            #     return re.search(regex, url).group(0)
            #
            # e = get_host_regex(response.url)
            # avg = None
            # sum = 0
            # if len(deny_domains.items())>0:
            #     for k,v in deny_domains.items():
            #         sum += v
            #     avg = sum // len(deny_domains.items())
            # if e in deny_domains and deny_domains[e] < 20:
            #     deny_domains[e] += 1
            # elif e in deny_domains and deny_domains[e] >= 20:
            #     deny_domains.pop(e)
            #     self.rules[0].link_extractor.deny_domains.add(e) # 此处害怕offsite 工作不正常
            # else:
            #     deny_domains[e] = 1