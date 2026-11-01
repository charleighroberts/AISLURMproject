from django.contrib import admin

from .models import AllowedDomain


@admin.register(AllowedDomain)
class AllowedDomainAdmin(admin.ModelAdmin):
    list_display = ["domain", "added_at"]
    search_fields = ["domain"]
