from django.contrib import admin
from .models import Portfolio, Asset, Transaction

class AssetInline(admin.TabularInline):
    model = Asset
    extra = 0

@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance')
    inlines = [AssetInline] # Позволит видеть акции сразу внутри портфеля

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('portfolio', 'action', 'stock', 'quantity', 'price', 'timestamp')
    list_filter = ('action', 'timestamp')