# -*- coding: utf-8 -*-

'''
Export the assessment to standard TREC style QREL files

assessment-export.py <save_qrels>
'''

import os
import re
import sys
import argparse
import traceback
import MySQLdb as mdb

# global variables

# table names
TABLE_TMPL = 'assess_%s'
QUERY_TABLE = TABLE_TMPL % 'query'
DOC_TABLE = TABLE_TMPL % 'document'
ASSESSMENT_TABLE = TABLE_TMPL % 'assessment'

DB_CON = None

query_dict = None
doc_dict = None
assessment_dict = None
qrels_dict = None

class MyDB(object) :
  '''
  Configuration of MySQL DB
  '''
  HOST = '127.0.0.1'
  PORT = 3306
  USER = 'xliu'
  PASSWD = 'who'
  #DB = 'xliu_cpeg657_14s_1'
  DB = 'xliu_cpeg657_14s_2'

def load_query () :
  '''
  Load the query table from DB into a dict
  '''
  try :
    print '[Info] Loading %s' % QUERY_TABLE
    global DB_CON

    db_cur = DB_CON.cursor()

    query_dict = dict()
    # fetch the whole query table at once, since it is small
    sql = 'SELECT * FROM %s' % QUERY_TABLE
    db_cur.execute(sql)
    rows = db_cur.fetchall()

    for row in rows :
      id = row[0]
      query_id = row[1]
      title = row[3]
      desc = row[4]

      item = dict()
      item['query_id'] = query_id
      item['title'] = title
      item['desc'] = desc
      query_dict[id] = item

    return query_dict
  except mdb.Error, e :
    print '[Error] SQL execution: %s' % sql
    print 'Error %d: %s' % (e.args[0],e.args[1])
    sys.exit(-1)

def load_doc () :
  '''
  Load the document table from DB into a dict
  '''
  try :
    print '[Info] Loading %s' % DOC_TABLE
    global DB_CON

    db_cur = DB_CON.cursor()

    doc_dict = dict()
    # fetch the document table, since it is huge, we need to fetch the
    # records one by one
    sql = 'SELECT * FROM %s' % DOC_TABLE
    db_cur.execute(sql)

    for i in range(db_cur.rowcount) :
      row = db_cur.fetchone()

      id = row[0]
      doc_id = row[1]

      item = dict()
      item['doc_id'] = doc_id
      doc_dict[id] = item

    return doc_dict
  except mdb.Error, e :
    print '[Error] SQL execution: %s' % sql
    print 'Error %d: %s' % (e.args[0],e.args[1])
    sys.exit(-1)

def load_assessment () :
  '''
  Load the assessment table from DB into a dict
  '''
  try :
    print '[Info] Loading %s' % DOC_TABLE
    global DB_CON

    db_cur = DB_CON.cursor()

    assessment_dict = dict()
    # fetch the assessment table, since it is huge, we need to fetch the
    # records one by one
    sql = 'SELECT * FROM %s' % ASSESSMENT_TABLE
    db_cur.execute(sql)

    for i in range(db_cur.rowcount) :
      row = db_cur.fetchone()

      id = row[0]
      qid = row[1]
      did = row[2]
      rel = row[4]

      item = dict()
      item['qid'] = qid
      item['did'] = did
      item['rel'] = rel
      assessment_dict[id] = item

    return assessment_dict
  except mdb.Error, e :
    print '[Error] SQL execution: %s' % sql
    print 'Error %d: %s' % (e.args[0],e.args[1])
    sys.exit(-1)

def save_qrels (file_path, qrels_list) :
  '''
  Save the qrels in standard TREC format

  file_path: string filesystem path to the qrels file
  qrels_list: the list of qrel items
  '''
  try :
    with open(file_path, 'w') as f :
      print 'Saving %s' % file_path
      qrels_list.sort(key=lambda x: int(x['query_id']))

      for qrel in qrels_list :
        record = '%s Q0 %s %s\n' %(qrel['query_id'], qrel['doc_id'],
            qrel['rel'])
        f.write(record)

  except IOError as e :
    print '-' * 60
    traceback.print_exc(file = sys.stdout)
    print '-' * 60
    sys.exit(-1)

  print '\nDone'

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

def main() :
  parser = argparse.ArgumentParser(description=__doc__, usage=__doc__)
  parser.add_argument('save_qrels')
  args = parser.parse_args()

  if os.path.isfile(args.save_qrels) :
    print '[Error] %s exists' % args.save_qrels
    return

  init_db()

  global query_dict
  global doc_dict
  global assessment_dict

  ## load query table
  query_dict = load_query()
  query_id_list = query_dict.keys()
  query_id_list.sort(key=lambda x: int(x))

  print '[Info] %10d queries loaded.' % len(query_dict)
  '''
  print '[Info] Dumping %s' % QUERY_TABLE
  for query_id in query_id_list :
    item = query_dict[query_id]
    print '%s - %s - %s' %(query_id, item['query_id'], item['title'])
  '''

  ## load document table
  doc_dict = load_doc()
  print '[Info] %10d documents loaded.' % len(doc_dict)

  ## import assessment table
  assessment_dict = load_assessment()
  print '[Info] %10d assessments loaded.' % len(assessment_dict)

  ## generate the qrels
  qrels_list = list()
  for id in assessment_dict :
    asm = assessment_dict[id]
    qid = asm['qid']
    did = asm['did']
    rel = asm['rel']
    if qid not in query_dict :
      print '[Error] Query ID %s not found in %s' %(qid, QUERY_TABLE)
      break
    if did not in doc_dict :
      print '[Error] Document ID %s not found in %s' %(did, DOC_TABLE)
      break
    item = dict()
    item['query_id'] = query_dict[qid]['query_id']
    item['doc_id'] = doc_dict[did]['doc_id']
    item['rel'] = asm['rel']
    qrels_list.append(item)

  ## save the qrels
  save_qrels(args.save_qrels, qrels_list)

  return

if '__main__' == __name__ :
  try :
    #test()
    main()
    close_db()
  except KeyboardInterrupt :
    print '\nGoodbye!'

