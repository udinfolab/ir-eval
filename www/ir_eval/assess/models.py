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
    return str(self.assessor) + "-" + str(self.index) + " : " + self.title

class Document(models.Model) :
  cw_id = models.CharField(max_length=100)
  header = models.TextField()
  title = models.TextField()
  html = models.TextField()

  def __unicode__(self) :
    return str(self.pk) + "-" + self.cw_id

class Assessment(models.Model) :
  query = models.ForeignKey(Query)
  document = models.ForeignKey(Document)
  has_assessed = models.BooleanField()
  is_rel = models.BooleanField()
  last_modified = models.CharField(max_length=100)

  def __unicode__(self) :
    return str(self.pk) + "-" + str(self.query.pk) + "-" \
      + str(self.document.cw_id)
