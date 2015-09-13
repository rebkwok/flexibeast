from django.contrib import admin

from website.models import Page, SubSection, Picture


class SubsectionInline(admin.TabularInline):
    model = SubSection
    extra = 1

class PictureInline(admin.TabularInline):
    model = Picture
    extra = 1

class PageAdmin(admin.ModelAdmin):
    model = Page
    inlines = (SubsectionInline, PictureInline)

admin.site.register(Page, PageAdmin)
