#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from django.db import models
from django.contrib.auth.models import User

import datetime
from django.utils import timezone

import uuid

class PDFInfo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pdfname  = models.CharField(default='', max_length=50, verbose_name="PDF名") # PDFファイル名
    numOfPages = models.IntegerField(default=0, verbose_name="ページ数")
    def __id__(self):
    	return str(self.id)
    def __str__(self):
    	return str(self.id)

class PageInfo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pdfinfo = models.ForeignKey(PDFInfo, models.SET_NULL, null=True, related_name="pdfinfos", related_query_name="pdfinfo")
    filename = models.CharField(default='', max_length=150) # 画像ファイル名
    height = models.FloatField(default=0.0)
    width = models.FloatField(default=0.0)
    page = models.IntegerField(default=0) # 画像の順番
    count = models.IntegerField(default=0) # 表示回数
    rotate = models.IntegerField(default=0)

    prev_page = models.ForeignKey('self', models.SET_NULL, related_name="prevs", related_query_name="prev", blank=True, null=True) # 同一文書の前の画像のID（ない場合は）
    next_page = models.ForeignKey('self', models.SET_NULL, related_name="nexts", related_query_name="next", blank=True, null=True) # 同一文書の前の画像のID（ない場合は）

    done = models.BooleanField(default=False)
    checkedAt = models.DateTimeField(default=None, blank=True, null=True)
    checkedBy   = models.ForeignKey(User, models.SET_NULL, default=None, related_name="pagecheckers", related_query_name="pagechecker", blank=True, null=True)

    def url(self):
    	return u'static/yoshida/images/pdf/' + self.filename
    def __id__(self):
    	return str(self.id)
    def __str__(self):
    	return str(self.id)

class LineInfo(models.Model):

    left = models.FloatField(default=0.0)
    top  = models.FloatField(default=0.0)
    height = models.FloatField(default=0.0)
    width  = models.FloatField(default=0.0)

    content = models.CharField(max_length=200, default=u'') # 内容
    fontsize = models.FloatField(default=0.0)
    writingmode = models.CharField(max_length=15, default=u'')
    letterspace = models.FloatField(default=0.0)

    pdfinfo = models.ForeignKey(PDFInfo, models.SET_NULL, null=True, related_name="parentpdfinfos", related_query_name="parentpdfinfo")
    pageinfo = models.ForeignKey(PageInfo, models.SET_NULL, default=None, related_name="pageinfos", related_query_name="pageinfo", blank=True, null=True)

    checkedAt = models.DateTimeField(default=None, blank=True, null=True)
    checkedBy = models.ForeignKey(User, models.SET_NULL, default=None, related_name="linecheckers", related_query_name="linechecker", blank=True, null=True)


    def overwrite(self, doc_dict):
    	self.left = doc_dict[u'left']
    	self.top = doc_dict[u'top']
    	self.width = doc_dict[u'width']
    	self.height = doc_dict[u'height']
    	self.content = doc_dict[u'content']
    	self.fontsize = doc_dict[u'fontsize']
    	self.writingmode = doc_dict[u'writingmode']
    	self.letterspace = doc_dict[u'letterspace']

    def __str__(self):
    	return u'LineInfo({0:d})'.format(self.pk)
