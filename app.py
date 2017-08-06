# -*- coding: utf-8 -*-
import math
import re
import time
import urllib2
import pymongo
from flask import Flask, request, render_template

# setting:
MONGODB_SERVER = '192.168.1.250'
MONGODB_PORT = 27017
MONGODB_DB = 'pkulaw'
MONGODB_COLLECTION_PKULAW = 'pkulaw_list'

ROWS_PER_PAGE = 20


app = Flask(__name__)

connection_string = "mongodb://%s:%d" % (MONGODB_SERVER, MONGODB_PORT)
content = {'mongodb_collection': MONGODB_COLLECTION_PKULAW, 'template_html': 'search.html'}

@app.route('/')
def index():
    return render_template('index.html', title=u'判决文书查询')

@app.route('/search', methods=['get'])
def search():
    keywords = request.args.get('keywords')
    page = int(request.args.get('page', 1))
    search_by_html = True if 'true' == request.args.get(
        'search_by_html', 'false').lower() else False
    #content_search_by = request.args.get('content_search_by', 'by_bugs')
    if page < 1:
        page = 1
    #search by elasticsearch or mongo
    page_info = search_mongodb(keywords, page, search_by_html)
    #
    return render_template('search.html', keywords=keywords, page_info=page_info, search_by_html=search_by_html, title=u'搜索结果-判决书搜索')

@app.route('/pnfl/<string:gid>', methods=['get'])
def pnfl(gid):
    client = pymongo.MongoClient(connection_string)
    db = client[MONGODB_DB]
    collection = db[MONGODB_COLLECTION_PKULAW]
    #search by elasticsearch or mongo
    result = collection.find_one({"gid":gid})
    print "gid:",gid#
    return result['html']
    #return render_template('result.html', result = result, title=u'判决书')
    
def search_mongodb(keywords, page, search_by_html):
    client = pymongo.MongoClient(connection_string)
    db = client[MONGODB_DB]
    keywords_regex = get_search_regex(keywords, search_by_html)
    collection = db[MONGODB_COLLECTION_PKULAW]
    # get the total count and page:
    total_rows = collection.find(keywords_regex).count()
    total_page = int(
        math.ceil(total_rows / (ROWS_PER_PAGE * 1.0)))
    page_info = {'current': page, 'total': total_page,
                 'total_rows': total_rows, 'rows': []}
    # get the page rows
    if total_page > 0 and page <= total_page:
        row_start = (page - 1) * ROWS_PER_PAGE
        cursors = collection.find(keywords_regex).skip(row_start).limit(ROWS_PER_PAGE)
        for c in cursors:
            #c['datetime'] = c['datetime'].strftime('%Y-%m-%d')
            #if 'gid' in c:
                # urlsep = c['url'].split('//')[1].split('/')
            #c['url'] = '%s-%s.html' % (urlsep[1], urlsep[2])
            page_info['rows'].append(c)
    client.close()
    return page_info

def get_search_regex(keywords, search_by_html):
    keywords_regex = {}
    kws = [ks for ks in keywords.strip().split(' ') if ks != '']
    field_name = 'html' if search_by_html else 'title'
    if len(kws) > 0:
        reg_pattern = re.compile('|'.join(kws), re.IGNORECASE)
        keywords_regex[field_name] = reg_pattern
    return keywords_regex
    
if __name__ == '__main__':
    app.run(host='0.0.0.0')
