# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy import *
from scrapy.loader import ItemLoader
from scrapy.loader.processors import MapCompose, TakeFirst
import re


class BroadcrawlerItem(Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    title = Field(

    )
    pubtime = Field(

    )
    url = Field(

    )
    content = Field(

    )
    author = Field(

    )
    _id = Field(

    )

class SimilarityItem(Item):
    title = Field(

    )
    content = Field(

    )
    ltitle = Field(

    )
    lcontent = Field(

    )
