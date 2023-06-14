from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from obcine.models import (
    Municipality,
    MunicipalityFinancialYear,
    FinancialYear,
    User,
    MunicipalityFinancialYear,
    PlannedExpenseDocument,
    MonthlyExpenseDocument,
    YearlyExpenseDocument,
    PlannedRevenueDocument,
    MonthlyRevenueDocument,
    YearlyRevenueDocument,
)

@receiver(post_save, sender=User)
def create_organization_for_user(sender, instance, created, **kwargs):
    # create empty municipality for user
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
    # create empty municipality financial year for all financial years
    if created:
        for year in FinancialYear.objects.all():
            MunicipalityFinancialYear(
                financial_year=year,
                municipality=instance,
                ).save()

@receiver(post_save, sender=FinancialYear)
def create_organization_financial_year_for_year(sender, instance, created, **kwargs):
    # create empty municipality financial year for all municipalities
    if created:
        for municipality in Municipality.objects.all():
            MunicipalityFinancialYear(
                financial_year=instance,
                municipality=municipality,
                ).save()

@receiver(post_save, sender=MunicipalityFinancialYear)
def create_municipality_documents_for_year(sender, instance, created, **kwargs):
    # create empty documents for municipality financial year
    if created:
        PlannedExpenseDocument(
            municipality_year=instance,
        ).save()
        MonthlyExpenseDocument(
            municipality_year=instance,
        ).save()
        YearlyExpenseDocument(
            municipality_year=instance,
        ).save()
        PlannedRevenueDocument(
            municipality_year=instance,
        ).save()
        MonthlyRevenueDocument(
            municipality_year=instance,
        ).save()
        YearlyRevenueDocument(
            municipality_year=instance,
        ).save()
