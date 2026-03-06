from django.contrib import admin
from .models import TelegramUser, Category, Product, Order, Cart, PromoCode

@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'full_name', 'username', 'balance', 'joined_at')
    search_fields = ('user_id', 'full_name', 'username')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'category', 'is_sold')
    list_filter = ('category', 'is_sold')

@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_percent', 'is_active')

admin.site.register(Order)
admin.site.register(Cart)
