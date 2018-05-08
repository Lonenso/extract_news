from scrapy.cmdline import execute
import sys
import os
from extract_news.patcher import Patcher
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
execute(['scrapy', 'crawl', 'sinanews'])
