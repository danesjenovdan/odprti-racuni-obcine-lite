from django.core.management.base import BaseCommand

from obcine.models import RevenueDefinition
from obcine.parse_utils import XLSCodesParser


class Command(BaseCommand):
    help = "Setup data"

    def handle(self, *args, **options):
        XLSCodesParser(RevenueDefinition)
