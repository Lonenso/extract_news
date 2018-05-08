import re

import copy

import logging

import datetime
from newspaper import network, urls, Article, Config
from newspaper.cleaners import DocumentCleaner
from newspaper.extractors import ContentExtractor, PIPE_SPLITTER, DASH_SPLITTER, UNDERSCORE_SPLITTER, ARROWS_SPLITTER, \
    SLASH_SPLITTER, MOTLEY_REPLACEMENT
import requests
from newspaper.article import ArticleDownloadState, log
from newspaper.outputformatters import OutputFormatter
from newspaper.utils import extract_meta_refresh
from dateutil.parser import parse as date_parser
import sys
import importlib
from newspaper.videos.extractors import VideoExtractor
from requests import Response
from scrapy import signals
from scrapy.exceptions import NotConfigured
from scrapy.http import HtmlResponse
import difflib

DATE_REGEX = r'([\./\-_]{0,1}(19|20)\d{2})[\./\-_]{0,1}(([0-3]{0,1}[0-9]|[A-Za-z]{3,5})[\./\-_]{0,1})([0-3]{0,1}[0-9])'
TIME_REGEX = r'(\d{2}:\d{2}:\d{2})'
FAIL_ENCODING = "ISO-8859-1"


logger = logging.getLogger(__name__)

class Patcher():
    @classmethod
    def from_crawler(cls, crawler):
        if not crawler.settings.getbool("PATCHER_ENABLED"):
            raise NotConfigured
        # get the number of items from settings

        # instantiate the extension object
        ext = cls()

        # connect the extension object to signals
        crawler.signals.connect(ext.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(ext.spider_closed, signal=signals.spider_closed)

        # return the extension object
        return ext

    def spider_opened(self, spider):
        logger.info("opened spider %s", spider.name)
        self.enable_patch()

    def spider_closed(self, spider):
        logger.info("closed spider %s", spider.name)

    def enable_patch(self):
        Article.download = download
        Article.parse = parse
        Article.is_news = None
        Config.fetch_videos = None
        ContentExtractor.get_publishing_date = get_publishing_date
        ContentExtractor.get_authors = get_authors
        ContentExtractor.get_title = get_title

    def disable_patch(self, name):
        del sys.modules[name]
        module = importlib.import_module(name)
        sys.modules[name] = module
        globals()[name] = module


def download(self, input_html=None, input_url=None, title=None, recursion_counter=0):
    """Downloads the link's HTML content, don't use if you are batch async
    downloading articles

    recursion_counter (currently 1) stops refreshes that are potentially
    infinite
    """
    """
    input_url here is to solve the problem that gives input_html and url could be none or wrong
    and add another method which gives response then return html to avoid messy code
    """
    # logger.debug("custom download")
    if input_html is None:
        try:
            html = network.get_html_2XX_only(self.url, self.config)
        except requests.exceptions.RequestException as e:
            self.download_state = ArticleDownloadState.FAILED_RESPONSE
            self.download_exception_msg = str(e)
            logger.warning('Download failed on URL %s because of %s' %
                      (self.url, self.download_exception_msg))
            return
    elif isinstance(input_html, (Response, HtmlResponse)):
        def _get_html_from_response(response):
            if response.encoding != FAIL_ENCODING:
                # return response as a unicode string
                html = response.text
            else:
                html = response.content
                if 'charset' not in response.headers.get('content-type'):
                    encodings = requests.utils.get_encodings_from_content(response.text)
                    if len(encodings) > 0:
                        response.encoding = encodings[0]
                        html = response.text
            return html or ''
        # logger.debug("Get HTML by delivering HTMLRESPONSE OR RESPONSE")
        html = _get_html_from_response(input_html)
        if html != '':
            self.url = input_html.url
    else:
        # logger.debug("Get HTML by delivering html's content")
        html = input_html
        if input_url is not None:
            self.url = input_url
        else:
            # logger.warning("input_url must not none")
            raise Exception("input_url must not none")

    if self.config.follow_meta_refresh:
        meta_refresh_url = extract_meta_refresh(html)
        if meta_refresh_url and recursion_counter < 1:
            return self.download(
                input_html=network.get_html(meta_refresh_url),
                recursion_counter=recursion_counter + 1)

    self.set_html(html)
    self.set_title(title)


def get_publishing_date(self, url, html, doc):
    """4 strategies for publishing date extraction. The strategies
    are descending in accuracy and the next strategy is only
    attempted if a preferred one fails.

    "Adjusted method order, we do care about time info

    1. Pubdate from metadata
    2. Raw regex searches in the HTML + added heuristics
    3. Pubdate from URL
    4. Assume this moment as published_date
    """
    # logger.debug("custom get publish date")
    def parse_date_str(date_str):
        if date_str:
            try:
                return date_parser(date_str)
            except (ValueError, OverflowError, AttributeError, TypeError):
                # logger.error("error occurs when parse date str: %s url: %s ",date_str, url)
                return None

    PUBLISH_DATE_TAGS = [
        {'attribute': 'property', 'value': 'rnews:datePublished',
         'content': 'content'},
        {'attribute': 'property', 'value': 'article:published_time',
         'content': 'content'},
        {'attribute': 'name', 'value': 'OriginalPublicationDate',
         'content': 'content'},
        {'attribute': 'itemprop', 'value': 'datePublished',
         'content': 'datetime'},
        {'attribute': 'property', 'value': 'og:published_time',
         'content': 'content'},
        {'attribute': 'name', 'value': 'article_date_original',
         'content': 'content'},
        {'attribute': 'name', 'value': 'publication_date',
         'content': 'content'},
        {'attribute': 'name', 'value': 'sailthru.date',
         'content': 'content'},
        {'attribute': 'name', 'value': 'PublishDate',
         'content': 'content'},
        {'attribute': 'pubdate', 'value': 'pubdate',
         'content': 'datetime'},
        {'attribute': 'itemprop', 'value': 'datePublished',
         'content': 'content'}
    ]
    for known_meta_tag in PUBLISH_DATE_TAGS:
        meta_tags = self.parser.getElementsByTag(
            doc,
            attr=known_meta_tag['attribute'],
            value=known_meta_tag['value'])
        if meta_tags:
            date_str = self.parser.getAttribute(
                meta_tags[0],
                known_meta_tag['content'])
            datetime_obj = parse_date_str(date_str)
            if datetime_obj:
                # logger.debug("extract date from meta")
                return datetime_obj

    date_match_fhtml = re.search(DATE_REGEX + " " + TIME_REGEX, html)
    # print(date_match_fhtml)
    if date_match_fhtml:
        date_str = date_match_fhtml.group(0)
        datetime_obj = parse_date_str(date_str)
        if datetime_obj:
            # logger.debug("extract date from html")
            return datetime_obj

    date_match = re.search(urls.STRICT_DATE_REGEX, url)
    if date_match:
        date_str = date_match.group(0)
        datetime_obj = parse_date_str(date_str)
        if datetime_obj:
            # logger.debug("extract date from url")
            return datetime_obj

    # debug for testing methods above
    # logger.debug("date from exactly now")
    return datetime.datetime.now()


def get_authors(self, doc):
    """Fetch the authors of the article, return as a list
    Only works for english articles
    """

    """
    Only add CUSTOM tag to extract authors
    """
    # logger.debug("custom get authors")

    _digits = re.compile('\d')

    def contains_digits(d):
        return bool(_digits.search(d))

    def uniqify_list(lst):
        """Remove duplicates from provided list but maintain original order.
          Derived from http://www.peterbe.com/plog/uniqifiers-benchmark
        """
        seen = {}
        result = []
        for item in lst:
            if item.lower() in seen:
                continue
            seen[item.lower()] = 1
            result.append(item.title())
        return result

    def parse_byline(search_str):
        """
        Takes a candidate line of html or text and
        extracts out the name(s) in list form:
        >>> parse_byline('<div>By: <strong>Lucas Ou-Yang</strong>,<strong>Alex Smith</strong></div>')
        ['Lucas Ou-Yang', 'Alex Smith']
        """
        # Remove HTML boilerplate
        search_str = re.sub('<[^<]+?>', '', search_str)

        # Remove original By statement
        search_str = re.sub('[bB][yY][\:\s]|[fF]rom[\:\s]', '', search_str)

        search_str = search_str.strip()

        # Chunk the line by non alphanumeric tokens (few name exceptions)
        # >>> re.split("[^\w\'\-\.]", "Tyler G. Jones, Lucas Ou, Dean O'Brian and Ronald")
        # ['Tyler', 'G.', 'Jones', '', 'Lucas', 'Ou', '', 'Dean', "O'Brian", 'and', 'Ronald']
        name_tokens = re.split("[^\w\'\-\.]", search_str)
        name_tokens = [s.strip() for s in name_tokens]

        _authors = []
        # List of first, last name tokens
        curname = []
        delimiters = ['and', ',', '']

        for token in name_tokens:
            if token in delimiters:
                if len(curname) > 0:
                    _authors.append(' '.join(curname))
                    curname = []

            elif not contains_digits(token):
                curname.append(token)

        # One last check at end
        valid_name = (len(curname) >= 2)
        if valid_name:
            _authors.append(' '.join(curname))

        return _authors

    # Try 1: Search popular author tags for authors

    ATTRS = ['name', 'rel', 'itemprop', 'class', 'id']
    VALS = ['author', 'byline', 'dc.creator','article-editor']
    matches = []
    authors = []

    for attr in ATTRS:
        for val in VALS:
            # found = doc.xpath('//*[@%s="%s"]' % (attr, val))
            found = self.parser.getElementsByTag(doc, attr=attr, value=val)
            matches.extend(found)

    for match in matches:
        content = ''
        if match.tag == 'meta':
            mm = match.xpath('@content')
            if len(mm) > 0:
                content = mm[0]
        else:
            content = match.text or ''
        if len(content) > 0:
            authors.extend(parse_byline(content))

    return uniqify_list(authors)

    # TODO Method 2: Search raw html for a by-line
    # match = re.search('By[\: ].*\\n|From[\: ].*\\n', html)
    # try:
    #    # Don't let zone be too long
    #    line = match.group(0)[:100]
    #    authors = parse_byline(line)
    # except:
    #    return [] # Failed to find anything
    # return authors


def parse(self):
    """
    Only change get_publish_date
    """
    # logger.debug("custom parse")
    self.throw_if_not_downloaded_verbose()

    self.doc = self.config.get_parser().fromstring(self.html)
    self.clean_doc = copy.deepcopy(self.doc)

    if self.doc is None:
        # `parse` call failed, return nothing
        return

    # TODO: Fix this, sync in our fix_url() method
    parse_candidate = self.get_parse_candidate()
    self.link_hash = parse_candidate.link_hash  # MD5

    document_cleaner = DocumentCleaner(self.config)
    output_formatter = OutputFormatter(self.config)

    title, is_news = self.extractor.get_title(self.clean_doc)
    self.set_title(title)
    self.is_news = is_news
    # if self.is_news == False:
    #     self.is_parsed = True
    #     return
    authors = self.extractor.get_authors(self.clean_doc)
    self.set_authors(authors)

    meta_lang = self.extractor.get_meta_lang(self.clean_doc)
    self.set_meta_language(meta_lang)

    if self.config.use_meta_language:
        self.extractor.update_language(self.meta_lang)
        output_formatter.update_language(self.meta_lang)

    meta_favicon = self.extractor.get_favicon(self.clean_doc)
    self.set_meta_favicon(meta_favicon)

    meta_description = \
        self.extractor.get_meta_description(self.clean_doc)
    self.set_meta_description(meta_description)

    canonical_link = self.extractor.get_canonical_link(
        self.url, self.clean_doc)
    self.set_canonical_link(canonical_link)

    tags = self.extractor.extract_tags(self.clean_doc)
    self.set_tags(tags)

    meta_keywords = self.extractor.get_meta_keywords(
        self.clean_doc)
    self.set_meta_keywords(meta_keywords)

    meta_data = self.extractor.get_meta_data(self.clean_doc)
    self.set_meta_data(meta_data)

    self.publish_date = self.extractor.get_publishing_date(
        self.url,
        self.html,
        self.clean_doc)

    # Before any computations on the body, clean DOM object
    self.doc = document_cleaner.clean(self.doc)

    self.top_node = self.extractor.calculate_best_node(self.doc)
    if self.top_node is not None:
        # 作者这里没有控制是否要提取video，我们这里有两种办法，一种是直接注释掉
        # 一种是加上控制
        if self.config.fetch_videos:
            video_extractor = VideoExtractor(self.config, self.top_node)
            self.set_movies(video_extractor.get_videos())

        self.top_node = self.extractor.post_cleanup(self.top_node)
        self.clean_top_node = copy.deepcopy(self.top_node)

        text, article_html = output_formatter.get_formatted(
            self.top_node)
        self.set_article_html(article_html)
        self.set_text(text)

    if self.config.fetch_images:
        self.fetch_images()

    self.is_parsed = True
    self.release_resources()


def get_title(self, doc):
    """Fetch the article title and analyze it

    Assumptions:
    - title tag is the most reliable (inherited from Goose)
    - h1, if properly detected, is the best (visible to users)
    - og:title and h1 can help improve the title extraction
    - python == is too strict, often we need to compare filtered
      versions, i.e. lowercase and ignoring special chars

    Explicit rules:
    1. title == h1, no need to split
    2. h1 similar to og:title, use h1
    3. title contains h1, title contains og:title, len(h1) > len(og:title), use h1
    4. title starts with og:title, use og:title
    5. use title, after splitting
    """
    title = ''
    title_element = self.parser.getElementsByTag(doc, tag='title')
    # no title found
    if title_element is None or len(title_element) == 0:
        return title, False

    # title elem found
    title_text = self.parser.getText(title_element[0])
    used_delimeter = False

    # title from h1
    # - extract the longest text from all h1 elements
    # - too short texts (fewer than 2 words) are discarded
    # - clean double spaces
    title_text_h1 = ''
    title_element_h1_list = self.parser.getElementsByTag(doc,
                                                         tag='h1') or []
    title_text_h1_list = [self.parser.getText(tag) for tag in
                          title_element_h1_list]
    if title_text_h1_list:
        # sort by len and set the longest
        title_text_h1_list.sort(key=len, reverse=True)
        title_text_h1 = title_text_h1_list[0]
        # discard too short texts
        # chinese news can not do this
        # if len(title_text_h1.split(' ')) <= 2:
        #     title_text_h1 = ''
        # clean double spaces
        title_text_h1 = ' '.join([x for x in title_text_h1.split() if x])


    def is_news_page(h1, title):
        if h1 == '' or h1 is None:
            return False
        else :
            similarity = difflib.SequenceMatcher(None, h1, title).quick_ratio()
            if similarity < 0.46:
                return False
            else:
                return True

    is_news = is_news_page(title_text_h1, title_text)


    # title from og:title
    title_text_fb = (
    self.get_meta_content(doc, 'meta[property="og:title"]') or
    self.get_meta_content(doc, 'meta[name="og:title"]') or '')

    # create filtered versions of title_text, title_text_h1, title_text_fb
    # for finer comparison
    filter_regex = re.compile(r'[^\u4e00-\u9fa5a-zA-Z0-9\ ]')
    filter_title_text = filter_regex.sub('', title_text).lower()
    filter_title_text_h1 = filter_regex.sub('', title_text_h1).lower()
    filter_title_text_fb = filter_regex.sub('', title_text_fb).lower()

    # check for better alternatives for title_text and possibly skip splitting
    if title_text_h1 == title_text:
        used_delimeter = True
    elif filter_title_text_h1 and filter_title_text_h1 == filter_title_text_fb:
        title_text = title_text_h1
        used_delimeter = True
    elif filter_title_text_h1 and filter_title_text_h1 in filter_title_text \
            and filter_title_text_fb and filter_title_text_fb in filter_title_text \
            and len(title_text_h1) > len(title_text_fb):
        title_text = title_text_h1
        used_delimeter = True
    elif filter_title_text_fb and filter_title_text_fb != filter_title_text \
            and filter_title_text.startswith(filter_title_text_fb):
        title_text = title_text_fb
        used_delimeter = True

    # split title with |
    if not used_delimeter and '|' in title_text:
        title_text = self.split_title(title_text, PIPE_SPLITTER,
                                      title_text_h1)
        used_delimeter = True

    # split title with -
    if not used_delimeter and '-' in title_text:
        title_text = self.split_title(title_text, DASH_SPLITTER,
                                      title_text_h1)
        used_delimeter = True

    # split title with _
    if not used_delimeter and '_' in title_text:
        title_text = self.split_title(title_text, UNDERSCORE_SPLITTER,
                                      title_text_h1)
        used_delimeter = True

    # split title with /
    if not used_delimeter and '/' in title_text:
        title_text = self.split_title(title_text, SLASH_SPLITTER,
                                      title_text_h1)
        used_delimeter = True

    # split title with »
    if not used_delimeter and ' » ' in title_text:
        title_text = self.split_title(title_text, ARROWS_SPLITTER,
                                      title_text_h1)
        used_delimeter = True

    title = MOTLEY_REPLACEMENT.replaceAll(title_text)

    # in some cases the final title is quite similar to title_text_h1
    # (either it differs for case, for special chars, or it's truncated)
    # in these cases, we prefer the title_text_h1
    filter_title = filter_regex.sub('', title).lower()
    if filter_title_text_h1 == filter_title:
        title = title_text_h1

    return title, is_news