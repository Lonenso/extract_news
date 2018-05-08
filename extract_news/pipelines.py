# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import codecs
import json

import logging
from scrapy.conf import settings
import pymongo
logger = logging.getLogger(__name__)


class ExtractNewsPipeline(object):
    def process_item(self, item, spider):
        return item

class JsonWithEncodingPipeline(object):
    # 自定义json文件的导出

    def __init__(self):
        self.file = codecs.open('sohuspider.json', 'w', encoding="utf-8")

    def process_item(self, item, spider):
        # discard too short title
        if len(item['title']) >= 15:
            lines = json.dumps(dict(item), ensure_ascii=False) + "\n"
            self.file.write(lines)
            return item
        else:
            print('DISCARD ITEM: ' + item['title']+'\n'+item['url'])
    def spider_closed(self, spider):
        self.file.close()

# class MongoPipeline(object):
#
#     collection_name = 'scrapy_items'
#
#     def __init__(self, mongo_uri, mongo_db):
#         self.mongo_uri = mongo_uri
#         self.mongo_db = mongo_db
#
#     @classmethod
#     def from_crawler(cls, crawler):
#         return cls(
#             mongo_uri=crawler.settings.get('MONGO_URI'),
#             mongo_db=crawler.settings.get('MONGO_DATABASE', 'items')
#         )
#
#     def open_spider(self, spider):
#         self.client = pymongo.MongoClient(self.mongo_uri)
#         self.db = self.client[self.mongo_db]
#
#     def close_spider(self, spider):
#         self.client.close()
#
#     def process_item(self, item, spider):
#         if len(item['title']) >= 15:
#             self.db[self.collection_name].insert_one(dict(item))
#             return item
#         else:
#             print('DISCARD ITEM: ' + item['title']+'\n'+item['url'])

class MongoPipeline(object):
    def __init__(self):
        host = settings["MONGODB_HOST"]
        port = settings["MONGODB_PORT"]
        dbname = settings["MONGODB_DBNAME"]
        sheetname = settings["MONGODB_SHEETNAME"]
        # 创建MONGODB数据库链接
        client = pymongo.MongoClient(host=host, port=port)
        # 指定数据库
        mydb = client[dbname]
        # 存放数据的数据库表名
        self.post = mydb[sheetname]

    def process_item(self, item, spider):
        data = dict(item)
        match_doc = self.post.find_one({"_id": data['_id']})
        #TODO: 过滤以及id判定
        if match_doc:
            logger.debug("document existed", data)
            # self.post.replace_one(match_doc, data)
        else:
            self.post.insert_one(data)
        return item
