from django.core.management.base import BaseCommand
from django.core.files import File

from obcine import models
from obcine.parse_utils import XLSCodesParser

from datetime import date

import os


class Command(BaseCommand):
    help = "Setup data"

    def handle(self, *args, **options):
        # this load and parses definitions from files/kode_matic.xlsx
        XLSCodesParser(models.RevenueDefinition)

        year2019 = models.FinancialYear(
            name="2019",
            start_date=date(day=1, month=1, year=2019),
            end_date=date(day=31, month=12, year=2019),
        )
        year2019.save()
        year2020 = models.FinancialYear(
            name="2020",
            start_date=date(day=1, month=1, year=2020),
            end_date=date(day=31, month=12, year=2020),
        )
        year2020.save()
        year2021 = models.FinancialYear(
            name="2021",
            start_date=date(day=1, month=1, year=2021),
            end_date=date(day=31, month=12, year=2021),
        )
        year2021.save()
        year2022 = models.FinancialYear(
            name="2022",
            start_date=date(day=1, month=1, year=2022),
            end_date=date(day=31, month=12, year=2022),
        )
        year2022.save()
        year2023 = models.FinancialYear(
            name="2023",
            start_date=date(day=1, month=1, year=2023),
            end_date=date(day=31, month=12, year=2023),
        )
        year2023.save()

        # on save signal runs and creates MunicipalityFinancialYear(s)
        municipality = models.Municipality(name="Testna občina")
        municipality.save()

        my2019 = models.MunicipalityFinancialYear.objects.get(
            financial_year=year2019, municipality=municipality
        )
        my2020 = models.MunicipalityFinancialYear.objects.get(
            financial_year=year2020, municipality=municipality
        )
        my2021 = models.MunicipalityFinancialYear.objects.get(
            financial_year=year2021, municipality=municipality
        )
        my2022 = models.MunicipalityFinancialYear.objects.get(
            financial_year=year2022, municipality=municipality
        )
        my2023 = models.MunicipalityFinancialYear.objects.get(
            financial_year=year2023, municipality=municipality
        )

        user = models.User(
            municipality=municipality,
            username="testniuser",
            email="test@test.dev",
        )
        user.save()
        user.set_password("spremenime")

        # -- upload files (we need to open the file every time because s3 closes the file after upload)

        ### Monthly reveues yanuar for each year

        with open("files/prihodki_apra.xlsx", "rb") as fi:
            my_file = File(fi, name=os.path.basename(fi.name))
            o = models.MonthlyRevenueDocument.objects.get(municipality_year=my2019)
            o.file=my_file
            o.save()
        with open("files/prihodki_apra.xlsx", "rb") as fi:
            my_file = File(fi, name=os.path.basename(fi.name))
            o = models.MonthlyRevenueDocument.objects.get(municipality_year=my2020)
            o.file=my_file
            o.save()
        with open("files/prihodki_apra.xlsx", "rb") as fi:
            my_file = File(fi, name=os.path.basename(fi.name))
            o = models.MonthlyRevenueDocument.objects.get(municipality_year=my2021)
            o.file=my_file
            o.save()
        with open("files/prihodki_apra.xlsx", "rb") as fi:
            my_file = File(fi, name=os.path.basename(fi.name))
            o = models.MonthlyRevenueDocument.objects.get(municipality_year=my2022)
            o.file=my_file
            o.save()
        with open("files/prihodki_apra.xlsx", "rb") as fi:
            my_file = File(fi, name=os.path.basename(fi.name))
            o = models.MonthlyRevenueDocument.objects.get(municipality_year=my2023)
            o.file=my_file
            o.save()

        ### Planned revenue for each year

        with open("files/prihodki_plan_apra.xlsx", "rb") as fi:
            my_file = File(fi, name=os.path.basename(fi.name))
            o = models.PlannedRevenueDocument.objects.get(municipality_year=my2019)
            o.file=my_file
            o.save()
        with open("files/prihodki_plan_apra.xlsx", "rb") as fi:
            my_file = File(fi, name=os.path.basename(fi.name))
            o = models.PlannedRevenueDocument.objects.get(municipality_year=my2020)
            o.file=my_file
            o.save()
        with open("files/prihodki_plan_apra.xlsx", "rb") as fi:
            my_file = File(fi, name=os.path.basename(fi.name))
            o = models.PlannedRevenueDocument.objects.get(municipality_year=my2021)
            o.file=my_file
            o.save()
        with open("files/prihodki_plan_apra.xlsx", "rb") as fi:
            my_file = File(fi, name=os.path.basename(fi.name))
            o = models.PlannedRevenueDocument.objects.get(municipality_year=my2022)
            o.file=my_file
            o.save()
        with open("files/prihodki_plan_apra.xlsx", "rb") as fi:
            my_file = File(fi, name=os.path.basename(fi.name))
            o = models.PlannedRevenueDocument.objects.get(municipality_year=my2023)
            o.file=my_file
            o.save()

        # Planned expanse

        with open("files/proracun_apra.xlsx", "rb") as fi:
            my_file = File(fi, name=os.path.basename(fi.name))
            o = models.PlannedExpenseDocument.objects.get(municipality_year=my2019)
            o.file=my_file
            o.save()
        with open("files/proracun_apra.xlsx", "rb") as fi:
            my_file = File(fi, name=os.path.basename(fi.name))
            o = models.PlannedExpenseDocument.objects.get(municipality_year=my2020)
            o.file=my_file
            o.save()
        with open("files/proracun_apra.xlsx", "rb") as fi:
            my_file = File(fi, name=os.path.basename(fi.name))
            o = models.PlannedExpenseDocument.objects.get(municipality_year=my2021)
            o.file=my_file
            o.save()
        with open("files/proracun_apra.xlsx", "rb") as fi:
            my_file = File(fi, name=os.path.basename(fi.name))
            o = models.PlannedExpenseDocument.objects.get(municipality_year=my2022)
            o.file=my_file
            o.save()
        with open("files/proracun_apra.xlsx", "rb") as fi:
            my_file = File(fi, name=os.path.basename(fi.name))
            o = models.PlannedExpenseDocument.objects.get(municipality_year=my2023)
            o.file=my_file
            o.save()

        # Monthly expanse

        with open("files/realizacija_apra.xlsx", "rb") as fi:
            my_file = File(fi, name=os.path.basename(fi.name))
            o = models.MonthlyExpenseDocument.objects.get(municipality_year=my2019)
            o.file=my_file
            o.save()
        with open("files/realizacija_apra.xlsx", "rb") as fi:
            my_file = File(fi, name=os.path.basename(fi.name))
            o = models.MonthlyExpenseDocument.objects.get(municipality_year=my2020)
            o.file=my_file
            o.save()
        with open("files/realizacija_apra.xlsx", "rb") as fi:
            my_file = File(fi, name=os.path.basename(fi.name))
            o = models.MonthlyExpenseDocument.objects.get(municipality_year=my2021)
            o.file=my_file
            o.save()
        with open("files/realizacija_apra.xlsx", "rb") as fi:
            my_file = File(fi, name=os.path.basename(fi.name))
            o = models.MonthlyExpenseDocument.objects.get(municipality_year=my2022)
            o.file=my_file
            o.save()
        with open("files/realizacija_apra.xlsx", "rb") as fi:
            my_file = File(fi, name=os.path.basename(fi.name))
            o = models.MonthlyExpenseDocument.objects.get(municipality_year=my2023)
            o.file=my_file
            o.save()

        ## yearly expanse

        # TODO fix files when come
        #files/real-zr-2020-apra-odhodki.xlsx
        #files/real-zr-2021-apra-odhodki.xlsx

        with open("files/proracun_apra.xlsx", "rb") as fi:
            my_file = File(fi, name=os.path.basename(fi.name))
            o = models.YearlyExpenseDocument.objects.get(municipality_year=my2019)
            o.file=my_file
            o.save()
        with open("files/proracun_apra.xlsx", "rb") as fi:
            my_file = File(fi, name=os.path.basename(fi.name))
            o = models.YearlyExpenseDocument.objects.get(municipality_year=my2020)
            o.file=my_file
            o.save()
        with open("files/proracun_apra.xlsx", "rb") as fi:
            my_file = File(fi, name=os.path.basename(fi.name))
            o = models.YearlyExpenseDocument.objects.get(municipality_year=my2021)
            o.file=my_file
            o.save()
        with open("files/proracun_apra.xlsx", "rb") as fi:
            my_file = File(fi, name=os.path.basename(fi.name))
            o = models.YearlyExpenseDocument.objects.get(municipality_year=my2022)
            o.file=my_file
            o.save()

        ## yearly revenue

        with open("files/real-zr-2020-apra-prihodki.xlsx", "rb") as fi:
            my_file = File(fi, name=os.path.basename(fi.name))
            o = models.YearlyRevenueDocument.objects.get(municipality_year=my2019)
            o.file=my_file
            o.save()
        with open("files/real-zr-2021-apra-prihodki.xlsx", "rb") as fi:
            my_file = File(fi, name=os.path.basename(fi.name))
            o = models.YearlyRevenueDocument.objects.get(municipality_year=my2020)
            o.file=my_file
            o.save()
        with open("files/real-zr-2020-apra-prihodki.xlsx", "rb") as fi:
            my_file = File(fi, name=os.path.basename(fi.name))
            o = models.YearlyRevenueDocument.objects.get(municipality_year=my2021)
            o.file=my_file
            o.save()
        with open("files/real-zr-2021-apra-prihodki.xlsx", "rb") as fi:
            my_file = File(fi, name=os.path.basename(fi.name))
            o = models.YearlyRevenueDocument.objects.get(municipality_year=my2022)
            o.file=my_file
            o.save()

        # -- end upload files

        # publish 2023 year
        my2023.is_published = True
        my2023.save()
