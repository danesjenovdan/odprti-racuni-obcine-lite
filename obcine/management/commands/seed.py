from django.core.management.base import BaseCommand
from django.core.files import File

from obcine import models
from obcine.parse_utils import XLSCodesParser

from datetime import date

import os


class Command(BaseCommand):
    help = 'Setup data'
    def handle(self, *args, **options):
        XLSCodesParser(models.RevenueDefinition)
        municipality = models.Municipality(name='Testna občina')
        municipality.save()
        user = models.User(
            municipality=municipality,
            username='testniuser',
            email='test@test.dev',
        )
        user.save()
        year2019 = models.FinancialYear(
            name='2019',
            start_date=date(day=1, month=1, year=2019),
            end_date=date(day=31, month=12, year=2019)
        )
        year2019.save()
        year2020 = models.FinancialYear(
            name='2020',
            start_date=date(day=1, month=1, year=2020),
            end_date=date(day=31, month=12, year=2020)
        )
        year2020.save()
        year2021 = models.FinancialYear(
            name='2021',
            start_date=date(day=1, month=1, year=2021),
            end_date=date(day=31, month=12, year=2021)
        )
        year2021.save()
        year2022 = models.FinancialYear(
            name='2022',
            start_date=date(day=1, month=1, year=2022),
            end_date=date(day=31, month=12, year=2022)
        )
        year2022.save()
        year2023 = models.FinancialYear(
            name='2023',
            start_date=date(day=1, month=1, year=2023),
            end_date=date(day=31, month=12, year=2023)
        )
        year2023.save()
        my1 = models.MunicipalityFinancialYear(
            financial_year=year2021,
            municipality=municipality
        )
        my1.save()
        my2 = models.MunicipalityFinancialYear(
            financial_year=year2022,
            municipality=municipality
        )
        my2.save()
        my3 = models.MunicipalityFinancialYear(
            financial_year=year2023,
            municipality=municipality
        )
        my3.save()


        with open('files/prihodki_apra.xlsx', 'rb') as fi:
            my_file = File(fi, name=os.path.basename(fi.name))
            models.MonthlyRevenueDocument(
                file=my_file,
                municipality_year=my1,
                municipality=municipality,
                year=year2019,
                month=models.Months.JANUAR
            ).save()
            models.MonthlyRevenueDocument(
                file=my_file,
                municipality_year=my1,
                municipality=municipality,
                year=year2020,
                month=models.Months.JANUAR
            ).save()
            models.MonthlyRevenueDocument(
                file=my_file,
                municipality_year=my1,
                municipality=municipality,
                year=year2021,
                month=models.Months.JANUAR
            ).save()
            models.MonthlyRevenueDocument(
                file=my_file,
                municipality_year=my2,
                municipality=municipality,
                year=year2022,
                month=models.Months.JANUAR
            ).save()
            models.MonthlyRevenueDocument(
                file=my_file,
                municipality_year=my3,
                municipality=municipality,
                year=year2023,
                month=models.Months.JANUAR
            ).save()

        with open('files/prihodki_plan_apra.xlsx', 'rb') as fi:
            my_file = File(fi, name=os.path.basename(fi.name))
            models.PlannedRevenueDocument(
                file=my_file,
                municipality_year=my1,
                municipality=municipality,
                year=year2019,
            ).save()
            models.PlannedRevenueDocument(
                file=my_file,
                municipality_year=my1,
                municipality=municipality,
                year=year2020,
            ).save()
            models.PlannedRevenueDocument(
                file=my_file,
                municipality_year=my1,
                municipality=municipality,
                year=year2021,
            ).save()
            models.PlannedRevenueDocument(
                file=my_file,
                municipality_year=my2,
                municipality=municipality,
                year=year2022,
            ).save()
            models.YearlyRevenueDocument(
                file=my_file,
                municipality_year=my2,
                municipality=municipality,
                year=year2022,
            ).save()
            models.PlannedRevenueDocument(
                file=my_file,
                municipality_year=my3,
                municipality=municipality,
                year=year2023,
            ).save()

        with open('files/proracun_apra.xlsx', 'rb') as fi:
            my_file = File(fi, name=os.path.basename(fi.name))
            models.PlannedExpenseDocument(
                file=my_file,
                municipality_year=my1,
                municipality=municipality,
                year=year2019,
            ).save()
            models.PlannedExpenseDocument(
                file=my_file,
                municipality_year=my1,
                municipality=municipality,
                year=year2020,
            ).save()
            models.PlannedExpenseDocument(
                file=my_file,
                municipality_year=my1,
                municipality=municipality,
                year=year2021,
            ).save()
            models.PlannedExpenseDocument(
                file=my_file,
                municipality_year=my2,
                municipality=municipality,
                year=year2022,
            ).save()
            models.YearlyExpenseDocument(
                file=my_file,
                municipality_year=my2,
                municipality=municipality,
                year=year2022,
            ).save()
            models.PlannedExpenseDocument(
                file=my_file,
                municipality_year=my3,
                municipality=municipality,
                year=year2023,
            ).save()

        with open('files/realizacija_apra.xlsx', 'rb') as fi:
            my_file = File(fi, name=os.path.basename(fi.name))
            models.MonthlyExpenseDocument(
                file=my_file,
                municipality_year=my1,
                municipality=municipality,
                year=year2019,
                month=models.Months.JANUAR
            ).save()
            models.MonthlyExpenseDocument(
                file=my_file,
                municipality_year=my1,
                municipality=municipality,
                year=year2020,
                month=models.Months.JANUAR
            ).save()
            models.MonthlyExpenseDocument(
                file=my_file,
                municipality_year=my1,
                municipality=municipality,
                year=year2021,
                month=models.Months.JANUAR
            ).save()
            models.MonthlyExpenseDocument(
                file=my_file,
                municipality_year=my2,
                municipality=municipality,
                year=year2022,
                month=models.Months.JANUAR
            ).save()
            models.MonthlyExpenseDocument(
                file=my_file,
                municipality_year=my3,
                municipality=municipality,
                year=year2023,
                month=models.Months.JANUAR
            ).save()
