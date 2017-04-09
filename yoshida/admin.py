from django.contrib import admin

from yoshida.models import PDFInfo, PageInfo, LineInfo

class PDFInfoAdmin(admin.ModelAdmin):
    list_display = ("pdfname", "numOfPages")
admin.site.register(PDFInfo, PDFInfoAdmin)

class PageInfoAdmin(admin.ModelAdmin):
    list_display = ("pdfinfo", "filename", "page", "count", "prev_page", "next_page", "checkedBy")
admin.site.register(PageInfo, PageInfoAdmin)

class LineInfoAdmin(admin.ModelAdmin):
    list_display = ("pdfinfo", "pageinfo", "left", "top", "width", "height", "checkedBy", "checkedAt")
admin.site.register(LineInfo, LineInfoAdmin)
