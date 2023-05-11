from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from obcine.models import Municipality, MunicipalityFinancialYear, FinancialYear, User

@receiver(post_save, sender=User)
def create_organization_for_user(sender, instance, created, **kwargs):
    if created:
        if not instance.municipality:
            municipality = Municipality(
                name=f'Zacasno ime za {instance.username}',
            )
            municipality.save()
            instance.municipality = municipality
            instance.save()

@receiver(post_save, sender=Municipality)
def create_organization_financial_year_for_organization(sender, instance, created, **kwargs):
    if created:
        for year in FinancialYear.objects.all():
            MunicipalityFinancialYear(
                financial_year=year,
                municipality=instance,
                ).save()

@receiver(post_save, sender=FinancialYear)
def create_organization_financial_year_for_year(sender, instance, created, **kwargs):
    if created:
        for municipality in Municipality.objects.all():
            MunicipalityFinancialYear(
                financial_year=instance,
                municipality=municipality,
                ).save()
