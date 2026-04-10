from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.admin import GroupAdmin as DjangoGroupAdmin
from django.contrib.auth.models import Group, User
from .models import Customer, FollowUp, Purchase, ProductType

admin.site.site_header = "Jai shree Fashion CRM Administration"
admin.site.site_title = "Jai shree Fashion CRM Admin"
admin.site.index_title = "Manage CRM Options"

try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

try:
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass


class FollowUpInline(admin.TabularInline):
    model = FollowUp
    extra = 0
    readonly_fields = ("next_followup_date", "status")
    fields = ("next_followup_date", "status", "notes")
    show_change_link = True


@admin.register(User)
class CustomUserAdmin(DjangoUserAdmin):
    pass


@admin.register(Group)
class CustomGroupAdmin(DjangoGroupAdmin):
    pass


@admin.register(ProductType)
class ProductTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "order")
    search_fields = ("name",)
    ordering = ("order", "name")
    list_editable = ("order",)
    list_per_page = 30


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "phone", "assigned_to", "created_at")
    list_filter = ("assigned_to", "created_at", "customer_type", "price_range")
    search_fields = ("name", "phone", "phone2", "whatsapp", "city", "notes", "address")
    date_hierarchy = "created_at"
    list_select_related = ("assigned_to",)
    list_per_page = 30
    autocomplete_fields = ("assigned_to", "product_interest")
    readonly_fields = ()
    inlines = (FollowUpInline,)


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ("customer", "amount", "date", "assigned_to")
    search_fields = ("customer__name", "customer__phone", "assigned_to__username", "assigned_to__email")
    list_filter = ("assigned_to", "date", "amount_range")
    date_hierarchy = "date"
    list_select_related = ("customer", "assigned_to")
    list_per_page = 30
    filter_horizontal = ("products",)
    autocomplete_fields = ("customer", "assigned_to")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("customer", "assigned_to").prefetch_related("products")


@admin.register(FollowUp)
class FollowUpAdmin(admin.ModelAdmin):
    list_display = ("customer", "next_followup_date", "status", "completed_at", "assigned_to")
    search_fields = ("customer__name", "customer__phone")
    list_filter = ("status", "completed_at", "next_followup_date", "assigned_to")
    date_hierarchy = "next_followup_date"
    list_select_related = ("customer", "assigned_to")
    list_per_page = 30
