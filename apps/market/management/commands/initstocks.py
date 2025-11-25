from django.core.management.base import BaseCommand
from apps.market.services import MoexDataService

class Command(BaseCommand):
    help = 'Initializes the database with a list of top stock tickers and their prices.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting MOEX stock data initialization..."))

        MoexDataService.initialize_top_stocks()

        self.stdout.write(self.style.SUCCESS("MOEX stock data initialization complete."))