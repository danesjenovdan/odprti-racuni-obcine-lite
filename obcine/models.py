from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from django.conf import settings

from mptt.models import MPTTModel, TreeForeignKey

from obcine.parse_utils import XLSXAppraBudget, XLSXAppraRevenue, download_image


def document_size_validator(value): # add this to some file where you can import it from
    limit = 10 * 1024 * 1024
    if value.size > limit:
        raise ValidationError('Datoteka je prevelika. Največja možna velikost je 10 MB.')

class Months(models.IntegerChoices):
        JANUAR = 1
        FEBRUAR = 2
        MAREC = 3
        APRIL = 4
        MAJ = 5
        JUNIJ = 6
        JULIJ = 7
        AVGUST = 8
        SEPTEMBER = 9
        OKTOBER = 10
        NOVEMBER = 11
        DECEMBER = 12


class Timestampable(models.Model):
    """
    An abstract base class model that provides self-updating
    ``created`` and ``modified`` fields.
    """
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        abstract = True


class Municipality(Timestampable):
    name = models.TextField(verbose_name=_('Nemo of municipality'))

    def __str__(self):
        return self.name


class User(AbstractUser, Timestampable):
    municipality = models.ForeignKey(
        'Municipality',
        blank=True,
        null=True,
        related_name='users',
        on_delete=models.SET_NULL,
        verbose_name=_('Municipality'))

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')


class FinancialYear(models.Model):
    name = models.TextField(verbose_name=_('Name'))
    start_date = models.DateField(verbose_name=_('Start date'))
    end_date = models.DateField(verbose_name=_('End date'))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Financial year')
        verbose_name_plural = _('Financial years')
        ordering = ['name']

class MunicipalityFinancialYear(models.Model):
    financial_year = models.ForeignKey('FinancialYear', on_delete=models.PROTECT)
    municipality = models.ForeignKey('Municipality', on_delete=models.PROTECT)

    def __str__(self):
        return f'{self.municipality.name}: {self.financial_year.name}'


class FinancialCategory(MPTTModel):
    name = models.CharField(max_length=256, verbose_name=_('Name'))
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='categories_children', verbose_name=_('Parent'))
    amount = models.DecimalField(decimal_places=2, max_digits=10, null=True, verbose_name=_('Amount'))
    order = models.IntegerField(verbose_name=_('Order'))
    instructions = models.TextField(verbose_name=_('Instructions'))
    code = models.TextField(verbose_name=_('Code'))

    def __str__(self):
        return self.name + ' ' + self.year.name

    def get_json_tree(self):
        return {
            'name': self.name,
            'amount': float(self.amount),
            'children': [child.get_json_tree() for child in self.get_children().order_by('order') if child.amount]
        }

    def to_json(self):
        return {
            'name': self.name,
            'amount': float(self.amount),
        }

    def get_offline_dict(self):
        """
        This method is used for generate modifed revenue dictionary
        """
        return {
            'name': self.name,
            'code': self.code,
            'children': self.children,
            'amount': self.amount,
            'parent_id': self.parent_id
        }

    class Meta:
        abstract = True

    class MPTTMeta:
        order_insertion_by = ['order']


## Revenue


class RevenueDefinition(MPTTModel):
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='categories_children', verbose_name=_('Parent'))
    name = models.CharField(max_length=256, verbose_name=_('Name'))
    code = models.TextField(verbose_name=_('Code'))
    order = models.IntegerField(verbose_name=_('Order'))

    def __str__(self):
        return f'{self.name}: {self.code}'

    @classmethod
    def get_id_value_dict(cls):
        return {revenue.id: revenue for revenue in cls.objects.all()}

    def get_offline_dict(self):
        """
        This method is used for generate modifed revenue dictionary
        """
        return {
            'name': self.name,
            'code': self.code,
            'children': self.children,
            'amount': self.amount,
            'parent_id': self.parent_id
        }


class PlannedRevenue(models.Model):
    name = models.CharField(max_length=256, verbose_name=_('Name'))
    code = models.TextField(verbose_name=_('Code'))
    definition = models.ForeignKey('RevenueDefinition', on_delete=models.CASCADE, related_name='%(class)s_related', verbose_name=_('RevenueDefinition'), null=True)
    municipality = models.ForeignKey('Municipality', on_delete=models.CASCADE, related_name='%(class)s_related', verbose_name=_('Organiaztion'))
    year = models.ForeignKey('FinancialYear', on_delete=models.CASCADE,null=True, blank=True, related_name='%(class)s_related', verbose_name=_('Year'))
    amount = models.DecimalField(decimal_places=2, max_digits=10, null=True, verbose_name=_('Amount'))
    document = models.ForeignKey('PlannedRevenueDocument', on_delete=models.CASCADE)


class MonthlyRevenue(models.Model):
    name = models.CharField(max_length=256, verbose_name=_('Name'))
    code = models.TextField(verbose_name=_('Code'))
    definition = models.ForeignKey('RevenueDefinition', on_delete=models.CASCADE, related_name='%(class)s_related', verbose_name=_('RevenueDefinition'))
    municipality = models.ForeignKey('Municipality', on_delete=models.CASCADE, related_name='monthly_revenue_realizations', verbose_name=_('Organiaztion'))
    year = models.ForeignKey('FinancialYear', on_delete=models.CASCADE,null=True, blank=True, related_name='monthly_revenue_realizations', verbose_name=_('Year'))
    month = models.IntegerField(choices=Months.choices, verbose_name=_('Month'))
    amount = models.DecimalField(decimal_places=2, max_digits=10, null=True, verbose_name=_('Amount'))
    document = models.ForeignKey('MonthlyRevenueDocument', on_delete=models.CASCADE)


class PlannedRevenueDocument(models.Model):
    file = models.FileField(
        verbose_name=_('File'),
        validators=[
            FileExtensionValidator(allowed_extensions=['xlsx']),
            document_size_validator
        ]
    )
    municipality_year = models.ForeignKey('MunicipalityFinancialYear', on_delete=models.CASCADE, related_name='revenue_documents', verbose_name=_('Municipality Financial Year'))
    municipality = models.ForeignKey('Municipality', on_delete=models.CASCADE, related_name='revenue_documents', verbose_name=_('Municipality'))
    year = models.ForeignKey('FinancialYear', on_delete=models.CASCADE, related_name='revenue_documents', verbose_name=_('Year'))

    def __str__(self):
        return f'{self.year.name}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        parser = XLSXAppraRevenue(self, PlannedRevenue, RevenueDefinition)
        if settings.ENABLE_S3:
            image_path = download_image(self.file.url, self.file.name)
            parser.parse_file(file_path=image_path)
        else:
            parser.parse_file(file_path=self.file.path)


    class Meta:
        unique_together = ('municipality', 'year')
        verbose_name = _('Planned revenue document')
        verbose_name_plural = _('Planned revenue documents')


class MonthlyRevenueDocument(models.Model):
    file = models.FileField(
        verbose_name=_('File'),
        validators=[
            FileExtensionValidator(allowed_extensions=['xlsx']),
            document_size_validator
        ]
    )
    municipality_year = models.ForeignKey('MunicipalityFinancialYear', on_delete=models.CASCADE, related_name='monthly_revenue_documents', verbose_name=_('Municipality Financial Year'))

    # TODO remove next 2 fields
    municipality = models.ForeignKey('Municipality', on_delete=models.CASCADE, related_name='monthly_revenue_documents', verbose_name=_('Municipality'))
    year = models.ForeignKey('FinancialYear', on_delete=models.CASCADE, related_name='monthly_revenue_documents', verbose_name=_('Year'))

    month = models.IntegerField(choices=Months.choices, verbose_name=_('Month'))

    def __str__(self):
        return f'{self.year.name}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        parser = XLSXAppraRevenue(self, MonthlyRevenue, RevenueDefinition, self.month)
        if settings.ENABLE_S3:
            image_path = download_image(self.file.url, self.file.name)
            parser.parse_file(file_path=image_path)
        else:
            parser.parse_file(file_path=self.file.path)


    class Meta:
        unique_together = ('municipality', 'year', 'month')
        verbose_name = _('Monthly revenue realization document')
        verbose_name_plural = _('Monthly revenue realization documents')


## Expense

class ExpenseDefinition(FinancialCategory):
    class Meta:
        verbose_name = _('Revenue definition')
        verbose_name_plural = _('Revenue definitions')


class PlannedExpense(FinancialCategory):
    municipality = models.ForeignKey('Municipality', on_delete=models.CASCADE, related_name='%(class)s_related', verbose_name=_('Organiaztion'))
    year = models.ForeignKey('FinancialYear', on_delete=models.CASCADE,null=True, blank=True, related_name='%(class)s_related', verbose_name=_('Year'))
    document = models.ForeignKey('PlannedExpenseDocument', on_delete=models.CASCADE)
    class Meta:
        verbose_name = _('Planned expense')
        verbose_name_plural = _('Planned expense')


class MonthlyExpense(FinancialCategory):
    municipality = models.ForeignKey('Municipality', on_delete=models.CASCADE, related_name='%(class)s_related', verbose_name=_('Organiaztion'))
    year = models.ForeignKey('FinancialYear', on_delete=models.CASCADE,null=True, blank=True, related_name='%(class)s_related', verbose_name=_('Year'))
    month = models.IntegerField(choices=Months.choices, verbose_name=_('Month'))
    document = models.ForeignKey('MonthlyExpenseDocument', on_delete=models.CASCADE)
    class Meta:
        verbose_name = _('Monthly expense')
        verbose_name_plural = _('Monthly expense')


class PlannedExpenseDocument(models.Model):
    file = models.FileField(
        verbose_name=_('File'),
        validators=[
            FileExtensionValidator(allowed_extensions=['xlsx']),
            document_size_validator
        ]
    )
    municipality_year = models.ForeignKey('MunicipalityFinancialYear', on_delete=models.CASCADE, related_name='expense_documents', verbose_name=_('Municipality Financial Year'))
    municipality = models.ForeignKey('Municipality', on_delete=models.CASCADE, related_name='expense_documents', verbose_name=_('Municipality'))
    year = models.ForeignKey('FinancialYear', on_delete=models.CASCADE, related_name='expense_documents', verbose_name=_('Year'))

    def __str__(self):
        return f'{self.year.name}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        parser = XLSXAppraBudget(self, PlannedExpense)
        if settings.ENABLE_S3:
            image_path = download_image(self.file.url, self.file.name)
            parser.parse_file(file_path=image_path)
        else:
            parser.parse_file(file_path=self.file.path)


    class Meta:
        unique_together = ('municipality', 'year')
        verbose_name = _('Planned expense document')
        verbose_name_plural = _('Planned expense documents')

class MonthlyExpenseDocument(models.Model):
    file = models.FileField(
        verbose_name=_('File'),
        validators=[
            FileExtensionValidator(allowed_extensions=['xlsx']),
            document_size_validator
        ]
    )
    municipality_year = models.ForeignKey('MunicipalityFinancialYear', on_delete=models.CASCADE, related_name='monthly_expense_documents', verbose_name=_('Municipality Financial Year'))
    municipality = models.ForeignKey('Municipality', on_delete=models.CASCADE, related_name='monthly_expense_documents', verbose_name=_('Municipality'))
    year = models.ForeignKey('FinancialYear', on_delete=models.CASCADE, related_name='monthly_expense_documents', verbose_name=_('Year'))
    month = models.IntegerField(choices=Months.choices, verbose_name=_('Month'))

    def __str__(self):
        return f'{self.year.name}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        parser = XLSXAppraBudget(self, MonthlyExpense, self.month)
        if settings.ENABLE_S3:
            image_path = download_image(self.file.url, self.file.name)
            parser.parse_file(file_path=image_path)
        else:
            parser.parse_file(file_path=self.file.path)


    class Meta:
        unique_together = ('municipality', 'year', 'month')
        verbose_name = _('Monthly expense realization document')
        verbose_name_plural = _('Monthly expense realization documents')
