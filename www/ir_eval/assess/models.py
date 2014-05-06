import datetime
from django.db import models
from django.contrib.auth.models import User

class Assessor(models.Model) :
  user = models.ForeignKey(User)
  name = models.CharField(max_length=100)

  def __unicode__(self) :
    return self.name
    #return self.user.username

class Query(models.Model) :
  qid = models.IntegerField()
  assessor = models.ForeignKey(Assessor)
  title = models.CharField(max_length=300)
  description = models.TextField()

  def __unicode__(self) :
    return str(self.assessor) + '-' + str(self.index) + " : " + self.title

class Document(models.Model) :
  doc_id = models.CharField(max_length=100)
  title = models.TextField()
  data = models.TextField()

  def __unicode__(self) :
    return str(self.pk) + '-' + self.doc_id

class Assessment(models.Model) :
  query = models.ForeignKey(Query)
  document = models.ForeignKey(Document)
  has_assessed = models.BooleanField()
  relevance = models.IntegerField()
  assessed_by = models.CharField(max_length=100)
  last_modified = models.CharField(max_length=100)

  def __unicode__(self) :
    return str(self.pk) + '-' + str(self.query.pk) + '-' \
      + str(self.document.doc_id)

class RetrievalFunction(models.Model) :
  user = models.ForeignKey(User)
  url = models.CharField(max_length=300)
  note = models.TextField()
  index = models.IntegerField()

  def __unicode__(self) :
    return str(self.user) + '-' + str(self.index)
        
class EvalItem(models.Model) :
  user = models.ForeignKey(User)
  rf = models.ForeignKey(RetrievalFunction)
  query = models.ForeignKey(Query)
  MAP = models.FloatField()
  P1 = models.FloatField()
  P3 = models.FloatField()
  P10 = models.FloatField()
  NDCG = models.FloatField()

  def __unicode__(self) :
    return str(self.pk) + '-' + str(self.rf)

class AvgEvalItem(models.Model) :
  user = models.ForeignKey(User)
  rf = models.ForeignKey(RetrievalFunction)
  MAP = models.FloatField()
  P1 = models.FloatField()
  P3 = models.FloatField()
  P10 = models.FloatField()
  NDCG = models.FloatField()

  def __unicode__(self) :
    return str(self.pk) + '-' + str(self.rf)
