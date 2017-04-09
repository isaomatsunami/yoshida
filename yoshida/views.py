# coding: utf-8

import json
import base64
import datetime
from django.utils import timezone

from collections import OrderedDict
from django.http import HttpResponse
from django.forms.models import modelform_factory
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required

from yoshida.models import PDFInfo, PageInfo, LineInfo

@login_required(login_url='/accounts/login/')
def main(request):
    pdfs = []
    for pdf in PDFInfo.objects.all():
        pdfs.append({'pdfinfo':pdf, 'pages': PageInfo.objects.filter(pdfinfo_id__exact=pdf.id ).order_by('page')})
    context = {'user': request.user, 'pdfs':pdfs}
    return render(request, 'yoshida/index.html', context)

@login_required(login_url='/accounts/login/')
def document(request, document_id):
    pdfinfo = get_object_or_404( PDFInfo, pk=document_id )
    context = {'user': request.user, "pdfinfo": pdfinfo, 'document_id': document_id}
    return render(request, 'yoshida/document.html', context)

@login_required(login_url='/accounts/login/')
def page(request, page_id):
    pageinfo = get_object_or_404( PageInfo, pk=page_id )
    context = {'user': request.user, "pdfinfo": pageinfo.pdfinfo, 'page_id': page_id}
    return render(request, 'yoshida/page.html', context)

@login_required(login_url='/accounts/login/')
def text(request, document_id):
    output = ''
    for page in PageInfo.objects.filter(pdfinfo_id__exact=document_id ).order_by('page'):
        for line in LineInfo.objects.filter(pageinfo_id__exact=page.id ).order_by('top'):
            output += line.content
    return HttpResponse(output)

""" RESTfulの規約
	GET /entries	エントリー一覧を取得する
	POST /entries	エントリーを追加する
	GET /entries/$entry_id	特定のエントリーを取得する
	PUT /entries/$entry_id	特定のエントリーを置き換える
	DELTE /entries/$entry_id	特定のエントリーを削除する
"""

def render_json_response(request, data, status=None):
    """responseをJSONで返す汎用関数"""
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    callback = request.GET.get('callback')
    if not callback:
        callback = request.POST.get('callback')  # POSTでJSONPの場合
    if callback:
        json_str = "%s(%s)" % (callback, json_str)
        response = HttpResponse(json_str, content_type='application/javascript; charset=UTF-8', status=status)
    else:
        response = HttpResponse(json_str, content_type='application/json; charset=UTF-8', status=status)
    return response

def pageinfo(request, id):
    """ PageInfoのREST """
    # print(request.method, id)
    if request.method == 'GET':
        if id == u'':
            # GETのパラメータにdocumentが付加されている場合だけ、そのdocumentのpageInfoを返す
            # GETのパラメータにpageが付加されている場合だけ、pageInfoを配列として返す
            pages = []
            if 'document' in request.GET:
                for page in PageInfo.objects.filter(pdfinfo_id__exact=request.GET['document'] ).order_by('page'):
                    prev_id = str(page.prev_page.id) if page.prev_page else None
                    next_id = str(page.next_page.id) if page.next_page else None
                    pages.append( OrderedDict([
                        ('id', page.__id__()),
                        ('next', next_id),
                        ('prev', prev_id),
                        ('page', page.page),
                        ('height', page.height),
                        ('width',  page.width),
                        ('url',  page.url()),
                        ('done',  page.done),
                    ]) )
                print("GET:all:", len(pages) )
            elif 'page' in request.GET:
                page = get_object_or_404( PageInfo, pk=request.GET['page'] )
                prev_id = str(page.prev_page.id) if page.prev_page else None
                next_id = str(page.next_page.id) if page.next_page else None
                pages.append( OrderedDict([
                    ('id', page.__id__()),
                    ('next', next_id),
                    ('prev', prev_id),
                    ('page', page.page),
                    ('height', page.height),
                    ('width',  page.width),
                    ('url',  page.url()),
                    ('done',  page.done),
                ]) )
                print("GET:single:")
            return render_json_response(request, pages)

        else:
            # idがあるなら、それを返す
            info = get_object_or_404( PageInfo, pk=id )
            info.count += 1
            info.save()
            prev_id = str(info.prev_page.id) if info.prev_page else None
            next_id = str(info.next_page.id) if info.next_page else None
            data = OrderedDict([
                    ('id', info.__id__()),
                    ('next', next_id),
                    ('prev', prev_id),
                    ('page', info.page),
                    ('height', info.height),
                    ('width',  info.width),
                    ('url',  info.url()),
                    ('done',  info.done),
                ])
            print("PDF:", info.__str__())
            return render_json_response(request, data)
    if request.method == 'PUT':
        # done要素だけ更新する
        info = get_object_or_404( PageInfo, pk=id )
        d = json.loads(request.body.decode('UTF-8'))
        info.done = d['done']
        info.checkedBy = request.user
        info.checkedAt = timezone.now()
        info.save()
        print("UPDATED:", info.__str__())
        return render_json_response(request, d)

def int_or_none(num):
    if num == None:
        return None
    try:
        # エラーが生じないのは小数点など数値、文字列の整数（文字列の少数はだめ）
        n = int(num)
    except ValueError:
        return None
    return n

def LineToDict(_line):
    return OrderedDict([
        ('id', _line.id),
        ('left', _line.left),
        ('top', _line.top),
        ('width', _line.width),
        ('height', _line.height),
        ('content', _line.content),
        ('fontsize', _line.fontsize),
        ('writingmode', _line.writingmode),
        ('letterspace', _line.letterspace),
        ('pageinfo', _line.pageinfo.__id__()),
    ])

def lineinfo(request, id):
    """
    	LineInfoのREST (https://tools.ietf.org/html/rfc7231#section-4.3)
    """
    # print(request.method, id)
    if request.method == 'GET':
        if id == u'':
            # GETのパラメータにdocumentが付加されている場合だけ、そのdocumentのLineInfoを返す
            # GETのパラメータにpageが付加されている場合だけ、そのpageのLineInfoを返す
            lines = []
            if 'document' in request.GET:
                for line in LineInfo.objects.filter(pdfinfo_id__exact=request.GET['document'] ):
                    lines.append( LineToDict(line) )
            elif 'page' in request.GET:
                for line in LineInfo.objects.filter(pageinfo_id__exact=request.GET['page'] ):
                    lines.append( LineToDict(line) )
            return render_json_response(request, lines)
        else:
            # idがあるなら、それを返す
            line = get_object_or_404( LineInfo, pk=id )
            return render_json_response(request, LineToDict(line))
    if request.method == 'POST':
        # 新規追加する
        d = json.loads( request.body.decode('UTF-8') )
        print(d)
        line = LineInfo(
        	# idはsaveするまでない
        	left=d[u'left'],
        	top=d[u'top'],
        	width=d[u'width'],
        	height=d[u'height'],
        	content=d[u'content'],
        	fontsize=d[u'fontsize'],
        	writingmode=d[u'writingmode'],
        	letterspace=d[u'letterspace']
        )
        line.pageinfo = get_object_or_404( PageInfo, pk=d[u'pageinfo'] )
        line.save()
        print("CREATED:", line.__str__())
        return render_json_response(request, LineToDict(line))

    if request.method == 'PUT':
        # 更新する
        line = get_object_or_404( LineInfo, pk=id )
        jsonData = json.loads(request.body.decode('UTF-8'))
        line.overwrite(jsonData)
        line.checkedBy = request.user
        line.checkedAt = timezone.now()
        line.save()
        print("UPDATED:", line.__str__())
        return render_json_response(request, LineToDict(line))

    if request.method == 'DELETE':
        # 削除する
        line = get_object_or_404( LineInfo, pk=id )
        print("DELETED:", line.__str__())
        line.delete()
        return render_json_response(request, {})

