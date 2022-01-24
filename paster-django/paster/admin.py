from django.contrib import admin
from django.apps import apps
from .models import *
from django.utils.html import format_html

unregister = ['paste', 'member']

app = apps.get_app_config('paster')

for model_name, model in app.models.items():
    if model_name in unregister:
        continue
    admin.site.register(model)


@admin.register(Paste)
class PasteAdmin(admin.ModelAdmin):
    list_display = ('anno', "tag", "cnt", "rating", "obj_link")
    list_filter = ('tags',)
    search_fields = ("text",)

    def anno(self, obj):
        return obj.anno

    def cnt(self, obj):
        return obj.cnt

    def rating(self, obj):
        return obj.rating

    def obj_link(self, obj):
        return obj.link_self or format_html('<span style="color: red;">{0}</span>', 'UNPOSTED')

    def tag(self, obj):
        return ', '.join([x.name for x in obj.tags.all()]) or format_html('<span style="color: red;">{0}</span>', 'UNTAGED')
    

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('name', "vk_id", "is_moder", "cnt")
    list_filter = ('is_moder',)
    search_fields = ("name", "vk_id")

    def cnt(self, obj):
        return obj.cnt
