from datetime import datetime
from importlib import import_module

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import gettext as _

from obcine.models import Task


class Command(BaseCommand):
    help = "Run "

    def handle(self, *args, **options):
        tasks = Task.objects.filter(started_at__isnull=True).order_by("created_at")
        msgs = []
        for task in tasks:
            # skip task if it's started in another runner
            check_task = Task.objects.get(id=task.id)
            if check_task.started_at:
                continue
            task.run()
