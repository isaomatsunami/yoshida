#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from yoshida.models import PDFInfo, PageInfo, LineInfo

import codecs, sys, os.path, re, math, urllib, glob
# pip install beautifulsoup4
# pip install lxml
import bs4
from bs4 import BeautifulSoup, element

pdfFiles = "yoshida/management/commands/pdf/*.pdf"
xmlFiles = "yoshida/management/commands/pdf/xmls/"

def parsePDFXML(fin):

	f_head, f_tail = os.path.split(fin)
	f_name = f_tail[:-4]

	pageOffsetX = 0
	pageOffsetY = 0
	nPages = 0
	pageObjects = []
	currentPage = None
	data = BeautifulSoup( open(fin, 'r').read(), "xml" )

	pdf = PDFInfo(pdfname=f_name, numOfPages=0)
	pdf.save()
	print(f_name)
	for page in data.find_all("page"):
		nPages += 1
		rotate = int(page['rotate'])
		bbox = [ float(n) for n in page['bbox'].split(',')]
		pageWidth = bbox[2]
		pageHeight = bbox[3]
		currentPage = PageInfo(
			pdfinfo=pdf,
			filename=f_name+"-"+str(nPages-1)+".jpg",
			height=pageHeight,
			width=pageWidth,
			page=nPages,
			rotate=rotate
		)
		currentPage.save()
		pageObjects.append(currentPage)
		print("  page : " + page['id'])

		for textbox in page.find_all('textbox'):
			for textline in textbox.find_all('textline'):
				textline_bbox = [ float(n) for n in textline['bbox'].split(',')]

				left = textline_bbox[0]
				width = textline_bbox[2] - left
				top = pageHeight - textline_bbox[3]
				height = textline_bbox[3] - textline_bbox[1]
				writing_mode = "horizontal-tb" if width > height else 'vertical-rl'

				content = ''
				fontsizes = []

				for text in textline.find_all('text'):
					if text.has_attr('size'):
						fontsizes.append( float(text['size']) )
					content = content + text.string

				mean_fontsize = int( sum(fontsizes) / len(fontsizes) )

				line = LineInfo(
					pdfinfo=pdf,
					width=width,height=height,top=top,left=left,
					content=content,fontsize=mean_fontsize,
					writingmode=writing_mode,letterspace=-0.1
				)
				line.pageinfo = currentPage
				line.save()

	pdf.numOfPages = nPages
	pdf.save()

	for i in range( nPages ):
		if i != 0:
			pageObjects[i].prev_page = pageObjects[i-1]
		if i != nPages - 1:
			pageObjects[i].next_page = pageObjects[i+1]
		pageObjects[i].save()

class Command(BaseCommand):
	def handle(self, *args, **options):
		# delete all
		print("deleting PDFInfos")
		for obj in PDFInfo.objects.all():
			obj.delete()
		print("deleting PageInfos")
		for obj in PageInfo.objects.all():
			obj.delete()
		print("deleting LineInfos")
		for obj in LineInfo.objects.all():
			obj.delete()
		print("loading pages....")
		for i, fin in enumerate( glob.glob( pdfFiles ) ):
			f_head, f_tail = os.path.split(fin)
			f_name = f_tail[:-4]
			xml_name = xmlFiles + f_name + ".xml"
			parsePDFXML(xml_name)


