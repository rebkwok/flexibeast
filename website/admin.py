from django.contrib import admin

from website.models import Page, Picture


class PictureInline(admin.TabularInline):
    model = Picture
    extra = 1

class PageAdmin(admin.ModelAdmin):
    model = Page
    inlines = (PictureInline,)

admin.site.register(Page, PageAdmin)
