#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import re
import sys
import csv
import json
import base64
import argparse
import traceback
import MySQLdb as mdb
import datetime
from collections import defaultdict

## Note: virtual environment required to import bs4
from bs4 import BeautifulSoup

# global variables
# file paths
# query
ASSESSOR_FILE = 'data/assessor.list'
QUERY_TITLE_FILE = 'data/query.title.list'
QUERY_DESC_FILE = 'data/query.desc.list'
# document
WARC_CORPUS_FILE = 'data/cochrane.warc'
DOC_RET_FILE = 'data/ret.list'
SPAM_LIST_FILE = 'data/spam.list'

# table names
TABLE_TMPL = 'assess_%s'
QUERY_TABLE = TABLE_TMPL % 'query'
DOC_TABLE = TABLE_TMPL % 'document'
ASSESSOR_TABLE = TABLE_TMPL % 'assessor'
ASSESSMENT_TABLE = TABLE_TMPL % 'assessment'

#RANK_THRED = 1
RANK_THRED = 50
SPAM_THRED = 70
DB_CON = None

assessor_dict = None
query_dict = None
query_desc_dict = None

spam_dict = None
doc_ret_dict = None
doc_id_dict = dict()

## reverse dict to look up for row-ID in DB
assessor_rev_dict = dict()
query_rev_dict = dict()
doc_rev_dict = dict()

class MyDB(object) :
  '''
  Configuration of MySQL DB
  '''
  HOST = '127.0.0.1'
  PORT = 3306
  USER = 'xliu'
  PASSWD = 'who'
  #DB = 'xliu_bias_1'
  DB = 'xliu_bias_2'

def load_assessor (file_path) :
  '''
  Load the assessor info

  file_path: string filesystem path to the assessor file
  '''
  try :
    with open(file_path) as assessor_file :
      print '[Info] Loading %s' % file_path

      assessor_dict = dict()
      for line in assessor_file :
        line = line.rstrip()
        row = line.split(' : ')
        if 4 != len(row) :
          print '[Error] Invalid assessor record: %s' % ' : '.join(row)
          continue

        id = row[0]

        item = dict()
        #item['user_id'] = int(row[0])
        item['user_name'] = row[1]
        item['passwd'] = row[2]
        item['full_name'] = row[3]
        assessor_dict[id] = item

      return assessor_dict
  except IOError as e :
    print '-' * 60
    traceback.print_exc(file = sys.stdout)
    print '-' * 60
    sys.exit(-1)

def load_query (file_path) :
  '''
  Load the query title file into a dict

  file_path: string filesystem path to the query file
  '''
  try :
    with open(file_path) as query_file :
      print '[Info] Loading %s' % file_path

      query_dict = dict()
      for line in query_file :
        line = line.rstrip()
        row = line.split(' : ')
        if 3 != len(row) :
          print '[Error] Invalid query record: %s' % ' : '.join(row)
          continue

        query_id = row[0]
        assessor_id = row[1]
        query_title = row[2]

        item = dict()
        item['assessor_id'] = assessor_id
        item['title'] = query_title
        query_dict[query_id] = item

      return query_dict
  except IOError as e :
    print '-' * 60
    traceback.print_exc(file = sys.stdout)
    print '-' * 60
    sys.exit(-1)

def load_spam_dict (file_path) :
  '''
  Load the spam list

  file_path: string filesystem path to the spam list file
  '''
  try :
    with open(file_path) as spam_file :
      print '[Info] Loading %s' % file_path

      spam_dict = dict()
      for line in spam_file :
        line = line.rstrip()
        row = line.split(' ')
        if 3 != len(row) :
          print '[Error] Invalid spamrecord: %s' % ' '.join(row)
          continue

        query_id = row[0]
        doc_id = row[1]
        score = int(row[2])
        spam_dict[doc_id] = score

      return spam_dict
  except IOError as e :
    print '-' * 60
    traceback.print_exc(file = sys.stdout)
    print '-' * 60
    sys.exit(-1)

def load_doc_ret_list (file_path) :
  '''
  Load the retrieval list for query-document map
  '''
  try :
    with open(file_path) as ret_file :
      print 'Loading %s' % file_path

      global spam_dict
      global doc_id_dict
      doc_ret_dict = defaultdict(dict)
      for line in ret_file :
        line = line.rstrip()
        row = line.split(' ')
        if 6 != len(row) :
          print '[Error] Invalid ret_list record: %s' % ' '.join(row)
          continue

        query_id = int(int(row[0]) / 10)
        doc_id = row[2]
        rank = int(row[3])

        if rank > RANK_THRED :
          continue

        ## for debug purpose only
        ## select one query only
        #if 1 != query_id :
          #continue

        if doc_id not in spam_dict :
          continue
        if spam_dict[doc_id] < SPAM_THRED :
          continue

        doc_ret_dict[query_id][doc_id] = 1
        doc_id_dict[doc_id] = 1

      return doc_ret_dict
  except IOError as e :
    print '-' * 60
    traceback.print_exc(file = sys.stdout)
    print '-' * 60
    sys.exit(-1)


def load_warc_corpus (file_path) :
  '''
  Load the corpus in WARC format

  file_path: string filesystem path to the corpus file
  '''
  global DB_CON
  db_cur = DB_CON.cursor()

  doc_imported = 0

  is_begin = False
  try:
    with open(file_path) as f:
      print '[Info] Loading %s' % file_path

      doc_id = ''
      str_list = []
      for line in f:
        #line = line.strip()
        if re.match(r'<DOC>', line):
          continue
        if re.match(r'<DOCNO> ', line):
          mo = re.match(r'<DOCNO> (.+) <\/DOCNO>', line)
          doc_id = mo.group(1)
          continue
        if re.match(r'<DOCHDR>', line):
          continue
        if re.match(r'<\/DOCHDR>', line):
          continue
        if re.match(r'<\/DOC>', line):
          ## import the document to DB
          doc_data = ''.join(str_list)

          if import_doc(db_cur, doc_id, doc_data) :
            doc_imported += 1

          ## clear the list: http://stackoverflow.com/a/850831/219617
          del str_list[:]
          # for debug purpose only
          #if doc_imported >= 500:
            #break

          ## perform commit every 1000 documents
          if 0 == doc_imported % 1000 :
            do_commit()
            ## for debug purpose only
            #break

        else:
          ## add the current string to str_list
          str_list.append(line)

  except IOError as e:
    print '-' * 60
    traceback.print_exec(file = sys.stdout)
    print '-' * 60
    exit(-1)

  do_commit()
  print '\n[Info] Summary:'
  print '[Info] %d documents imported' % doc_imported

def import_doc(db_cur, doc_id, doc_data) :
  '''
  Import one document to DB
  '''
  global doc_rev_dict
  global doc_id_dict

  # skip documents not in the doc_ret_dict
  if doc_id not in doc_id_dict :
    return False

  (header, html) = process_warc(doc_data)
  title = extract_title(html)

  # in rare situation, the title will be blank. We need to fix it.
  if '' == title :
    title = 'N/A'

  # apply base64 encoding, therefore base64 decoding should be applied
  # when data is fetched from DB
  #title = title.decode('ascii', 'replace')
  #html = html.decode('ascii', 'replace')
  #title = unicode(title, errors = 'ignore')
  #html = unicode(html, errors = 'ignore')
  title_b64 = base64.b64encode(remove_non_ascii(title))
  html_b64 = base64.b64encode(remove_non_ascii(html))

  #print '[Info]: importing %s' % doc_id

  sql = 'INSERT INTO %s(cw_id,header,title,html) VALUES'\
        '(' % DOC_TABLE
  sql += '%s, %s, %s, %s)'
  try :
    db_cur.execute(sql, (doc_id, header, title_b64, html_b64))
    #db_cur.execute(sql, (doc_id, header, title, html))
    # http://stackoverflow.com/a/3790542
    doc_rev_dict[doc_id] = db_cur.lastrowid
    return True
  except mdb.Error, e:
    print '[Error] SQL execution: %s' % sql
    print 'Error %d: %s' % (e.args[0],e.args[1])
    return False

def remove_non_ascii(s) :
  '''
  remove non-ASCII characters
  http://stackoverflow.com/a/1342373/219617
  '''
  if not (s is None) :
    return ''.join(filter(lambda x: ord(x)<128, s))
  else :
    return ''

def process_warc(html) :
  '''
  Sepearate the HTTP header and body from WARC dump
  '''
  header_list = []
  body_list = []
  in_body = False
  for line in html.split('\n'):
    ## if the line starts with a '<' tag, it should be an identification
    ## of HTML body
    if re.match(r'<', line):
      in_body = True

    if in_body:
      body_list.append(line)
    else :
      header_list.append(line)

  header_str = '\n'.join(header_list)
  body_str = '\n'.join(body_list)
  return (header_str, body_str)

def extract_title(html) :
  '''
  Extract the title of HTML
  '''
  soup = BeautifulSoup(html)
  if None == soup :
    return 'N/A'
  if None == soup.html :
    # malformed html
    return 'N/A'
  if None == soup.html.head :
    # this should not happen
    return 'N/A'
  if None == soup.html.head.title :
    # this should not happen either
    return 'N/A'
  return soup.html.head.title.string

def test_db() :
  '''
  An example to test the connection of DB
  http://zetcode.com/db/mysqlpython/
  '''
  try :
    con = mdb.connect(host=MyDB.HOST, port=MyDB.PORT, user=MyDB.USER,
        passwd=MyDB.PASSWD, db=MyDB.DB)
    cur = con.cursor()
    cur.execute('SELECT VERSION()')
    ver = cur.fetchone()
    print '[Info] Database version : %s ' % ver

  except mdb.Error, e:
    print 'Error %d: %s' % (e.args[0],e.args[1])
    sys.exit(1)

  finally :
    if con :
      con.close()

def test() :
  test_db()

def init_db() :
  try :
    global DB_CON
    DB_CON = mdb.connect(host=MyDB.HOST, port=MyDB.PORT, user=MyDB.USER,
        passwd=MyDB.PASSWD, db=MyDB.DB)
    if DB_CON :
      print '[Info] DB connection initialized'
    else :
      print '[Error] DB connection failed. Will exit.'
      sys.exit(-1)

  except mdb.Error, e:
    print 'Error %d: %s' % (e.args[0],e.args[1])
    if DB_CON :
      DB_CON.close()
    sys.exit(1)

def close_db() :
  global DB_CON
  if DB_CON :
    DB_CON.close()
    DB_CON = None

def sql_execute(cur, sql) :
  '''
  Execute SQL on DB

  cur: the cursor
  sql: the SQL statement
  '''
  try :
    cur.execute(sql)
    return True
  except mdb.Error, e :
    print '[Error] SQL execution: %s' % sql
    print '%d: %s' %(e.args[0], e.args[1])
    return False

def do_commit() :
  '''
  Commit the current transaction
  '''
  try :
    DB_CON.commit()
  except mdb.Error, e :
    print '[Error] Commit - %d: %s' %(e.args[0], e.args[1])
    DB_CON.rollback()
    return False

def main() :
  init_db()

  global assessor_dict
  global query_dict
  global query_desc_dict

  global spam_dict
  global doc_ret_dict

  global assessor_rev_dict
  global query_rev_dict
  global doc_rev_dict

  ## improt assessor
  assessor_dict = load_assessor(ASSESSOR_FILE)
  assessor_id_list = assessor_dict.keys()
  assessor_id_list.sort(key=lambda x: int(x))

  db_cur = DB_CON.cursor()
  print '[Info] Importing %s' % ASSESSOR_TABLE
  for id in assessor_id_list :
    user_id = int(id)
    name = assessor_dict[id]['full_name']

    sql = 'INSERT INTO %s(user_id,name) VALUES(%d,' \
        % (ASSESSOR_TABLE, user_id)
    sql += '%s)'
    try :
      db_cur.execute(sql, (name,))
      # http://stackoverflow.com/a/3790542
      assessor_rev_dict[id] = db_cur.lastrowid
    except mdb.Error, e:
      print '[Error] SQL execution: %s' % sql
      print 'Error %d: %s' % (e.args[0],e.args[1])
      sys.exit(-1)

  do_commit()
  # for debug purpose only
  #return



  ## import query
  query_dict = load_query(QUERY_TITLE_FILE)
  #query_desc_dict = load_query_desc(QUERY_DESC_FILE)
  query_id_list = query_dict.keys()
  query_id_list.sort(key=lambda x: int(x))

  db_cur = DB_CON.cursor()
  print '[Info] Importing %s' % QUERY_TABLE
  for query_id in query_id_list :
    assessor_id = query_dict[query_id]['assessor_id']
    title = query_dict[query_id]['title']
    #desc = query_desc_dict[query_id]
    desc = 'N/A'

    sql = 'INSERT INTO %s(qid,assessor_id,title,description)'\
        'VALUES(%s,%s,' %(QUERY_TABLE, query_id, assessor_id)
    sql += '%s,%s)'
    try :
      db_cur.execute(sql, (title, desc))
      # http://stackoverflow.com/a/3790542
      query_rev_dict[int(query_id)] = db_cur.lastrowid
    except mdb.Error, e:
      print '[Error] SQL execution: %s' % sql
      print 'Error %d: %s' % (e.args[0],e.args[1])
      sys.exit(-1)

  do_commit()
  # for debug purpose only
  #return



  #'''
  ## import documents
  spam_dict = load_spam_dict(SPAM_LIST_FILE)
  doc_ret_dict = load_doc_ret_list(DOC_RET_FILE)

  sum_num = 0
  print 'Query : # Document statistics'
  for query_id in doc_ret_dict :
    doc_num = len(doc_ret_dict[query_id].keys())
    print '%s : %d' %(query_id, doc_num)
    sum_num += doc_num
  print 'all : %d' % sum_num

  # for debug purpose only
  #return

  print '[Info] Importing %s' % DOC_TABLE
  load_warc_corpus(WARC_CORPUS_FILE)



  ## import assessment table
  db_cur = DB_CON.cursor()
  print '[Info] Importing %s' % ASSESSMENT_TABLE
  for query_id in doc_ret_dict :
    if query_id not in query_rev_dict :
      print '[Error] query_id not found in query_rev_dict: %s' % query_id
      continue
    query_row_id = query_rev_dict[query_id]

    for doc_id in doc_ret_dict[query_id] :
      if doc_id not in doc_rev_dict :
        print '[Error] doc_id not found in doc_rev_dict: %s' % doc_id
        continue
      doc_row_id = doc_rev_dict[doc_id]

      sql = 'INSERT INTO %s(query_id,document_id,has_assessed,is_rel,'\
          'polarity,last_modified) VALUES(' \
          %(ASSESSMENT_TABLE)
      sql += '%s, %s, %s, %s, %s, %s)'
      try :
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db_cur.execute(sql, (query_row_id, doc_row_id, False, False,
          -1, now))
      except mdb.Error, e:
        print '[Error] SQL execution: %s' % sql
        print 'Error %d: %s' % (e.args[0],e.args[1])
        sys.exit(-1)

  do_commit()
  return

if '__main__' == __name__ :
  try :
    #test()
    main()
    close_db()
  except KeyboardInterrupt :
    print '\nGoodbye!'

