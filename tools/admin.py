from django.contrib import admin

from tools.models import DeviceType

# Register your models here.
class DeviceTypeViewAdmin(admin.ModelAdmin):
    list_display = ('manufacturer', 'model')
admin.site.register(DeviceType, DeviceTypeViewAdmin)
