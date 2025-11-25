from django.contrib import admin
from .models import Stock

@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('ticker', 'name', 'current_price', 'lot_size', 'updated_at')
    search_fields = ('ticker', 'name')