from django.contrib import admin
from .models import Customer, FollowUp, Purchase, ProductType

admin.site.site_header = "25Carat CRM Administration"
admin.site.site_title = "25Carat CRM Admin"
admin.site.index_title = "Manage CRM Options"


class FollowUpInline(admin.TabularInline):
    model = FollowUp
    extra = 0
    readonly_fields = ("next_followup_date", "status")
    fields = ("next_followup_date", "status", "notes")
    show_change_link = True


@admin.register(ProductType)
class ProductTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "order")
    search_fields = ("name",)
    ordering = ("order", "name")
    list_editable = ("order",)
    list_per_page = 30


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "city",
        "phone",
        "phone2",
        "whatsapp",
        "assigned_to",
        "latest_purchase_date",
    )
    list_filter = ("assigned_to", "created_at")
    search_fields = ("name", "phone", "phone2", "whatsapp", "city", "notes")
    date_hierarchy = "created_at"
    list_select_related = ("assigned_to",)
    list_per_page = 30
    readonly_fields = ("created_at", "total_spent", "latest_purchase_date")
    inlines = (FollowUpInline,)
    fieldsets = (
        ("Customer details", {
            "fields": (
                "name",
                "city",
                "phone",
                "whatsapp",
                "phone2",
                "assigned_to",
            )
        }),
        ("Notes", {
            "fields": ("notes",),
            "classes": ("collapse",),
        }),
        ("System info", {
            "fields": ("created_at", "latest_purchase_date", "total_spent"),
            "classes": ("collapse",),
        }),
    )


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ("customer", "amount_range", "amount", "date", "assigned_to", "products_display")
    search_fields = ("customer__name", "customer__phone", "products__name")
    list_filter = ("assigned_to", "date", "amount_range", "products")
    date_hierarchy = "date"
    list_select_related = ("customer", "assigned_to")
    list_per_page = 30
    filter_horizontal = ("products",)

    def products_display(self, obj):
        return obj.product_summary() or "-"

    products_display.short_description = "Products"


@admin.register(FollowUp)
class FollowUpAdmin(admin.ModelAdmin):
    list_display = ("customer", "next_followup_date", "status", "completed_at", "assigned_to", "customer_phone")
    search_fields = ("customer__name", "customer__phone")
    list_filter = ("status", "completed_at", "next_followup_date", "assigned_to")
    date_hierarchy = "next_followup_date"
    list_select_related = ("customer", "assigned_to")
    list_per_page = 30

    def customer_phone(self, obj):
        return obj.customer.phone

    customer_phone.short_description = "Phone"
