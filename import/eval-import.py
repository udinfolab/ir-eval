# -*- coding: utf-8 -*-

'''
Import the evaluation resutls (retrieval functions, eval, avg_eval)
into DB
'''

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

# global variables
# file paths
# query
RET_FUNC_FILE = 'data/rf.list'
EVAL_FILE = 'data/eval.list'
AVG_EVAL_FILE = 'data/avg_eval.list'

# table names
TABLE_TMPL = 'assess_%s'
ASSESSOR_TABLE = TABLE_TMPL % 'assessor'
QUERY_TABLE = TABLE_TMPL % 'query'
RET_FUNC_TABLE = TABLE_TMPL % 'retrievalfunction'
EVAL_TABLE = TABLE_TMPL % 'evalitem'
AVG_EVAL_TABLE = TABLE_TMPL % 'avgevalitem'

DB_CON = None

assessor_dict = None
query_dict = None
ret_func_dict = None

## reverse dict to look up for row-ID in DB

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

      query_dict[query_id] = id

    return query_dict
  except mdb.Error, e :
    print '[Error] SQL execution: %s' % sql
    print 'Error %d: %s' % (e.args[0],e.args[1])
    sys.exit(-1)

def load_assessor () :
  '''
  Load the assessor table from DB into a dict
  '''
  try :
    print '[Info] Loading %s' % ASSESSOR_TABLE
    global DB_CON

    db_cur = DB_CON.cursor()

    assessor_dict = dict()
    # fetch the whole assessor table at once, since it is small
    sql = 'SELECT * FROM %s' % ASSESSOR_TABLE
    db_cur.execute(sql)
    rows = db_cur.fetchall()

    for row in rows :
      id = row[0]
      user_id = row[1]

      assessor_dict[user_id] = id

    return assessor_dict
  except mdb.Error, e :
    print '[Error] SQL execution: %s' % sql
    print 'Error %d: %s' % (e.args[0],e.args[1])
    sys.exit(-1)

def load_ret_func_list (file_path) :
  '''
  Load the retrieval funciton list
  '''
  sep = ' : '
  try :
    with open(file_path) as ret_func_file :
      print 'Loading %s' % file_path

      ret_func_dict = dict()
      for line in ret_func_file :
        line = line.rstrip()
        # skip comments
        if re.match('#', line) :
          continue
        # skip empty lines
        if re.match(r'^$', line) :
          continue

        row = line.split(sep)
        if 3 > len(row) :
          print '[Error] Invalid ref_func_list record: %s' \
            % sep.join(row)
          continue

        id = row[0]
        assessor_id = row[1]
        rf_id = row[2]
        note = 'N/A'
        if 4 == len(row) :
          note = row[3]

        item = dict()
        item['assessor_id'] = assessor_id
        item['rf_id'] = rf_id
        item['note'] = note
        ret_func_dict[id] = item

      return ret_func_dict
  except IOError as e :
    print '-' * 60
    traceback.print_exc(file = sys.stdout)
    print '-' * 60
    sys.exit(-1)

def load_eval_list (file_path) :
  '''
  Load the eval item list
  '''
  sep = ' '
  try :
    with open(file_path) as eval_file :
      print 'Loading %s' % file_path

      eval_list = list()
      for line in eval_file :
        line = line.rstrip()
        # skip comments
        if re.match('#', line) :
          continue
        # skip empty lines
        if re.match(r'^$', line) :
          continue

        row = line.split(sep)
        if 5 != len(row) :
          print '[Error] Invalid eval_list record: %s' % sep.join(row)
          continue

        rf_id = row[0]
        qid = row[1]
        map = row[2]
        p5 = row[3]
        ndcg = row[4]

        item = dict()
        item['rf_id'] = rf_id
        item['qid'] = qid
        item['map'] = map
        item['p5'] = p5
        item['ndcg'] = ndcg
        eval_list.append(item)

      return eval_list
  except IOError as e :
    print '-' * 60
    traceback.print_exc(file = sys.stdout)
    print '-' * 60
    sys.exit(-1)

def load_avg_eval_list (file_path) :
  '''
  Load the avg eval item list
  '''
  sep = ' '
  try :
    with open(file_path) as avg_eval_file :
      print 'Loading %s' % file_path

      avg_eval_list = list()
      for line in avg_eval_file :
        line = line.rstrip()
        # skip comments
        if re.match('#', line) :
          continue
        # skip empty lines
        if re.match(r'^$', line) :
          continue

        row = line.split(sep)
        if 5 != len(row) :
          print '[Error] Invalid avg_eval_list record: %s' % sep.join(row)
          continue

        rf_id = row[0]
        map = row[1]
        p5 = row[2]
        ndcg = row[3]
        ndcg_o = row[4]

        item = dict()
        item['rf_id'] = rf_id
        item['map'] = map
        item['p5'] = p5
        item['ndcg'] = ndcg
        item['ndcg_o'] = ndcg_o
        avg_eval_list.append(item)

      return avg_eval_list
  except IOError as e :
    print '-' * 60
    traceback.print_exc(file = sys.stdout)
    print '-' * 60
    sys.exit(-1)

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

  #disable import to avoid data been overwritten
  return

  # load query table
  query_dict = load_query()

  # load assessor table
  assessor_dict = load_assessor()

  # load retrieval function lsit
  ret_func_dict = load_ret_func_list(RET_FUNC_FILE)

  # load eval item list
  eval_list = load_eval_list(EVAL_FILE)

  # load avg eval item list
  avg_eval_list = load_avg_eval_list(AVG_EVAL_FILE)

  ## improt retrieval function table
  rf_rev_dict = dict()

  db_cur = DB_CON.cursor()
  print '[Info] Importing %s' % RET_FUNC_TABLE
  rf_id_list = ret_func_dict.keys()
  rf_id_list.sort(key=lambda x: int(x))

  for id in rf_id_list :
    item = ret_func_dict[id]
    assessor_id = int(item['assessor_id'])
    if assessor_id not in assessor_dict :
      print '[Error] assessor_id %d not found in assessor_dict'\
        % assessor_id
      sys.exit(-1)

    user_id = assessor_dict[assessor_id]
    url = ''
    note = item['note']
    rf_id = item['rf_id']

    sql = 'INSERT INTO %s(user_id, url, note, rf_id) VALUES'\
      % RET_FUNC_TABLE
    sql += '(%s, %s, %s, %s)'

    try :
      db_cur.execute(sql, (user_id, url, note, rf_id))
      # http://stackoverflow.com/a/3790542
      rf_rev_dict[rf_id] = db_cur.lastrowid
    except mdb.Error, e:
      print '[Error] SQL execution: %s' % sql
      print 'Error %d: %s' % (e.args[0],e.args[1])
      sys.exit(-1)

  do_commit()

  # import eval item table
  db_cur = DB_CON.cursor()
  print '[Info] Importing %s' % EVAL_TABLE

  for item in eval_list :
    rf_id = item['rf_id']
    if rf_id not in rf_rev_dict :
      print '[Error] rf_id %s not found in rf_rev_dict' % rf_id
      sys.exit(-1)
    rf_pk = rf_rev_dict[rf_id]

    qid = int(item['qid'])
    if qid not in query_dict :
      print '[Error] qid %s not found in query_dict' % qid
      sys.exit(-1)
    query_pk = query_dict[qid]

    sql = 'INSERT INTO %s(rf_id, query_id, MAP, P5, nDCG) VALUES'\
      % EVAL_TABLE
    sql += '(%s, %s, %s, %s, %s)'

    try :
      db_cur.execute(sql, (rf_pk, query_pk, item['map'], item['p5'],
        item['ndcg']))
    except mdb.Error, e:
      print '[Error] SQL execution: %s' % sql
      print 'Error %d: %s' % (e.args[0],e.args[1])
      sys.exit(-1)

  do_commit()

  # import avg eval item table
  db_cur = DB_CON.cursor()
  print '[Info] Importing %s' % AVG_EVAL_TABLE

  for item in avg_eval_list :
    rf_id = item['rf_id']
    if rf_id not in rf_rev_dict :
      print '[Error] rf_id %s not found in rf_rev_dict' % rf_id
      sys.exit(-1)
    rf_pk = rf_rev_dict[rf_id]

    sql = 'INSERT INTO %s(rf_id, MAP, P5, nDCG, nDCG_o) VALUES'\
      % AVG_EVAL_TABLE
    sql += '(%s, %s, %s, %s, %s)'

    try :
      db_cur.execute(sql, (rf_pk, item['map'], item['p5'],
        item['ndcg'], item['ndcg_o']))
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

