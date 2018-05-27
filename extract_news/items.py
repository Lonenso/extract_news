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
    """
    l means lens
    h1_title_siml means similarity between h1 tag and title tag and so on 
    
    This item aims to record similarity which uses any kinds of sequenceMatcher between elements from page.
    Our goal is to extract news page firmly and quickily from lots of pages.
    So We need to keep url, title, content, h1, (actually we can use our own algorithm)
    I think if we parse a page's content, and we've been spending time on parsing, and resources have been cost.
    So it's better to find a way avoid extracting content but it can quickily juage a page is news or not. 
    """
    url = Field(

    )
    title = Field(

    )
    content = Field(

    )
    pubtime = Field(

    )
    h1 = Field(

    )
    ltitle = Field(

    )
    lcontent = Field(

    )
    h1_title_siml = Field(

    )
    title_content_siml = Field(

    )
    _id = Field(

    )
    weight = Field(

    )
    is_news = Field(

    )
    judge = Field(

    )


