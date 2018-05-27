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

deny_regex = 'slide|blog|auto|weibo|baby|vip|book|picture|photo|video|tags|comment'

deny_domains = {}

class simlSpider(CrawlSpider):
    name = 'simlspider'
    start_urls = ["http://news.sina.com.cn/"]
    allowed_domains = ['sina.com.cn']
    # base_url = 'http://roll.news.sina.com.cn/s/channel.php?ch=01#col=90,91,92&spec=&type=&ch=01&k=&offset_page=0&offset_num=0&num=80&asc=&page={0}'

    rules = (
        Rule(LinkExtractor(allow=(),), follow=True, callback='parse_news'),
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
        item = SimilarityItem()
        article = Article(url='', config=config)
        article.download(input_html=response)
        article.parse()
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
        if article.text and article.text != '':
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
                logger.error("a:{0} b:{1}".format(a, b))
        item['h1_title_siml'] = foo(article.h1, article.title)
        item['_id'] = hashlib.md5(response.url.encode('utf-8')).hexdigest()
        item['weight'] = article.weight
        item['judge'] = 2
        item['is_news'] = article.get_is_news()
        yield item



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