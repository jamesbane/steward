from django.contrib import admin

from tools.models import DeviceType

# Register your models here.
class DeviceTypeViewAdmin(admin.ModelAdmin):
    list_display = ('manufacturer', 'model', 'identity_device_profile_type')
admin.site.register(DeviceType, DeviceTypeViewAdmin)