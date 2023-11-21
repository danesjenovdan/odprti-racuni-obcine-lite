from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator
from django.conf import settings
from django.contrib.contenttypes.models import ContentType

from importlib import import_module

from mptt.models import MPTTModel, TreeForeignKey
from martor.models import MartorField

from datetime import datetime

from obcine.parse_utils import XLSXAppraBudget, XLSXAppraRevenue, download_file
from obcine.validators import (
    document_size_validator,
    image_validator,
    validate_image_extension,
    validate_expanse_file,
    validate_revenue_file
)


class Timestampable(models.Model):
    """
    An abstract base class model that provides self-updating
    ``created`` and ``modified`` fields.
    """
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        abstract = True


class Task(Timestampable):
    started_at = models.DateTimeField(
        help_text='time when started',
        blank=True,
        null=True,
        default=None
    )
    finished_at = models.DateTimeField(
        help_text='time when finished',
        blank=True,
        null=True,
        default=None
    )
    errored_at = models.DateTimeField(
        help_text='time when errored',
        blank=True,
        null=True,
        default=None
    )
    error_msg = models.TextField()
    name = models.TextField(blank=False, null=False, help_text='Name of task')
    email_msg = models.TextField(blank=False, null=False, help_text='A message sent to the administrator when the task is complete.')
    payload = models.JSONField(help_text='Payload kwargs')


    def run(self):
        self.started_at = datetime.now()
        self.save()
        try:
            data = self.payload
            model = data['model']
            parser = data['parser']
            definition = data.get('definition', None)
            pk = data['pk']
            self_model = data['self']

            models_module = import_module('obcine.models')
            parser_module = import_module('obcine.parse_utils')

            models_class = getattr(models_module, model)
            document_class = getattr(models_module, self_model)
            parser_class = getattr(parser_module, parser)

            document = document_class.objects.get(id=pk)

            if definition and definition != 'None':
                definiton_model = getattr(models_module, definition)
                parser = parser_class(
                    document,
                    model=models_class,
                    definiton_model=definiton_model
                )
            else:
                parser = parser_class(
                    document,
                    model=models_class,
                    definiton_model=None
                )
            if settings.ENABLE_S3:
                image_path = download_file(document.file.url, document.file.name)
                parser.parse_file(file_path=image_path)
            else:
                parser.parse_file(file_path=document.file.path)

            self.finished_at = datetime.now()
            self.save()

        except Exception as e:
            self.errored_at = datetime.now()
            self.error_msg = e
            self.save()


class ParsableDocument(Timestampable):
    municipality_year = models.ForeignKey('MunicipalityFinancialYear', on_delete=models.CASCADE, related_name='%(class)s_related', verbose_name=_('Municipality Financial Year'))

    file = models.FileField(
        verbose_name=_('File'),
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['xlsx']),
            document_size_validator
        ]
    )

    def parse(self, parser, model, definition=None):
        if definition:
            definition = definition.__name__
        Task(
            name='Parse xls',
            payload={
                'model': f'{model.__name__}',
                'parser': f'{parser.__name__}',
                'definition': f'{definition}',
                'pk': self.id,
                'self': f'{self.__class__.__name__}',
            }
        ).save()
        # parser = parser(self, model, definition)
        # if settings.ENABLE_S3:
        #     image_path = download_file(self.file.url, self.file.name)
        #     parser.parse_file(file_path=image_path)
        # else:
        #     parser.parse_file(file_path=self.file.path)

    class Meta:
        abstract = True

class RevenueParsableDocument(ParsableDocument):
    file = models.FileField(
        verbose_name=_('File'),
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['xlsx']),
            document_size_validator,
            validate_revenue_file
        ]
    )

    class Meta:
        abstract = True

class ExpenseParsableDocument(ParsableDocument):
    file = models.FileField(
        verbose_name=_('File'),
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['xlsx']),
            document_size_validator,
            validate_expanse_file
        ]
    )

    class Meta:
        abstract = True

class Municipality(Timestampable):
    name = models.TextField(verbose_name=_('Nemo of municipality'))
    slug = models.SlugField(verbose_name=_('Slug'), unique=True)
    financial_years = models.ManyToManyField('FinancialYear', through='MunicipalityFinancialYear')
    link = models.URLField(null=True, blank=True, verbose_name=_('Organization\'s link'))
    logo = models.ImageField(
        null=True, blank=True,
        verbose_name=_('Logo'),
        validators=[image_validator, validate_image_extension])

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Municipality')
        verbose_name_plural = _('Municipality')


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

    def is_current(self):
        """
        this method return True if year is current or in future
        """
        try:
            return datetime.now().year <= int(self.name)
        except:
            return False

    class Meta:
        verbose_name = _('Financial year')
        verbose_name_plural = _('Financial years')
        ordering = ['name']


class MunicipalityFinancialYear(Timestampable):
    class BType(models.TextChoices):
        PROPOSAL = "PROPOSAL", _("Predlog proračuna")
        REBALANS = "REBALANS", _("Rebalans proračuna")
        VALID = "VALID", _("Veljavni proračun")
        ADOPTED = "ADOPTED", _("Sprejeti proračun")
    financial_year = models.ForeignKey('FinancialYear', verbose_name=_('Leto'),  related_name='municipalityfinancialyears', on_delete=models.PROTECT)
    municipality = models.ForeignKey('Municipality', related_name='municipalityfinancialyears', on_delete=models.PROTECT)
    budget_date = models.DateField(verbose_name=_('Datum proračuna'), null=True, blank=True)
    budget_type = models.CharField(
        max_length=20,
        choices=BType.choices,
        default=BType.VALID,
        verbose_name=_('Tip proračuna')
    )
    is_published = models.BooleanField(default=False, verbose_name=_('Javno prikazano leto'))

    def __str__(self):
        return f'{self.municipality.name}: {self.financial_year.name}'

    class Meta:
        verbose_name = _('Municipality financial year')
        verbose_name_plural = _('Municipality financial year')


class FinancialCategory(MPTTModel):
    name = models.CharField(max_length=256, verbose_name=_('Name'))
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='categories_children', verbose_name=_('Parent'))
    amount = models.DecimalField(decimal_places=2, max_digits=10, null=True, verbose_name=_('Amount'))
    order = models.IntegerField(verbose_name=_('Order'))
    instructions = models.TextField(verbose_name=_('Instructions'))
    code = models.TextField(verbose_name=_('Code'))

    def __str__(self):
        return self.name + ' ' #+ self.year.name

    def get_json_tree(self):
        return {
            'name': self.name,
            'code': self.code,
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
            'children': self.children if hasattr(self, 'children') else [],
            'amount': self.amount,
            'parent_id': self.parent_id
        }
    def get_offline_dict_keyed_children(self):
        """
        This method is used for generate modifed revenue dictionary
        """
        return {
            'name': self.name,
            'code': self.code,
            'children': {i['code']: i for i in self.children} if hasattr(self, 'children') else {},
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

    def get_offline_dict_keyed_children(self):
        """
        This method is used for generate modifed revenue dictionary
        """
        return {
            'name': self.name,
            'code': self.code,
            'children': {i['code']: i for i in self.children},
            'amount': self.amount,
            'parent_id': self.parent_id
        }


class Revenue(Timestampable):
    name = models.CharField(max_length=256, verbose_name=_('Name'))
    code = models.TextField(verbose_name=_('Code'))
    definition = models.ForeignKey('RevenueDefinition', on_delete=models.CASCADE, related_name='%(class)s_related', verbose_name=_('RevenueDefinition'), null=True)
    municipality = models.ForeignKey('Municipality', on_delete=models.CASCADE, related_name='%(class)s_related', verbose_name=_('Organiaztion'))
    year = models.ForeignKey('FinancialYear', on_delete=models.CASCADE,null=True, blank=True, related_name='%(class)s_related', verbose_name=_('Year'))
    amount = models.DecimalField(decimal_places=2, max_digits=10, null=True, verbose_name=_('Amount'))

    class Meta:
        abstract = True


class PlannedRevenue(Revenue):
    document = models.ForeignKey('PlannedRevenueDocument', on_delete=models.CASCADE, related_name='children')


class YearlyRevenue(Revenue):
    document = models.ForeignKey('YearlyRevenueDocument', on_delete=models.CASCADE)


class MonthlyRevenue(Revenue):
    document = models.ForeignKey('MonthlyRevenueDocument', on_delete=models.CASCADE)


class PlannedRevenueDocument(RevenueParsableDocument):
    def __str__(self):
        return f'{self.municipality_year.financial_year.name}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # TODO check if its needed
        # delete data if file reupload
        # self.children.all().delete()
        if self.file:
            self.parse(
                parser=XLSXAppraRevenue,
                model=PlannedRevenue,
                definition=RevenueDefinition
            )

    class Meta:
        unique_together = ['municipality_year']
        verbose_name = _('Planned revenue document')
        verbose_name_plural = _('Planned revenue documents')


class YearlyRevenueDocument(RevenueParsableDocument):
    timestamp = models.DateField(verbose_name=_('Datum obdelave podatkov'), null=True, blank=True)

    def __str__(self):
        return f'{self.municipality_year.financial_year.name}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.file:
            self.parse(
                parser=XLSXAppraRevenue,
                model=YearlyRevenue,
                definition=RevenueDefinition
            )

    class Meta:
        unique_together = ['municipality_year']
        verbose_name = _('Yearly revenue document')
        verbose_name_plural = _('Yearly revenue documents')


class MonthlyRevenueDocument(RevenueParsableDocument):
    timestamp = models.DateField(verbose_name=_('Datum obdelave podatkov'), null=True, blank=True)

    def __str__(self):
        return f'{self.municipality_year.financial_year.name}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.file:
            self.parse(
                parser=XLSXAppraRevenue,
                model=MonthlyRevenue,
                definition=RevenueDefinition,
            )

    class Meta:
        unique_together = ['municipality_year']
        verbose_name = _('Monthly revenue realization document')
        verbose_name_plural = _('Monthly revenue realization documents')


## Expense

class ExpenseDefinition(FinancialCategory):
    class Meta:
        verbose_name = _('Revenue definition')
        verbose_name_plural = _('Revenue definitions')


class Expense(FinancialCategory):
    municipality = models.ForeignKey('Municipality', on_delete=models.CASCADE, related_name='%(class)s_related', verbose_name=_('Organiaztion'))
    year = models.ForeignKey('FinancialYear', on_delete=models.CASCADE,null=True, blank=True, related_name='%(class)s_related', verbose_name=_('Year'))
    class Meta:
        abstract = True


class PlannedExpense(Expense):
    document = models.ForeignKey('PlannedExpenseDocument', on_delete=models.CASCADE, related_name='children')
    class Meta:
        verbose_name = _('Planned expense')
        verbose_name_plural = _('Planned expense')


class YearlyExpense(Expense):
    document = models.ForeignKey('YearlyExpenseDocument', on_delete=models.CASCADE)
    class Meta:
        verbose_name = _('Yearly expense')
        verbose_name_plural = _('Yearly expense')


class MonthlyExpense(Expense):
    document = models.ForeignKey('MonthlyExpenseDocument', on_delete=models.CASCADE)
    class Meta:
        verbose_name = _('Monthly expense')
        verbose_name_plural = _('Monthly expense')


class PlannedExpenseDocument(ExpenseParsableDocument):
    def __str__(self):
        return f'{self.municipality_year.financial_year.name}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # TODO check if its needed
        # delete data if file reupload
        #self.children.all().delete()
        if self.file:
            self.parse(
                parser=XLSXAppraBudget,
                model=PlannedExpense,
            )

    class Meta:
        unique_together = ['municipality_year']
        verbose_name = _('Planned expense document')
        verbose_name_plural = _('Planned expense documents')


class MonthlyExpenseDocument(ExpenseParsableDocument):
    timestamp = models.DateField(verbose_name=_('Datum obdelave podatkov'), null=True, blank=True)

    def __str__(self):
        return f'{self.municipality_year.financial_year.name}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.file:
            self.parse(
                parser=XLSXAppraBudget,
                model=MonthlyExpense,
            )

    class Meta:
        unique_together = ['municipality_year']
        verbose_name = _('Monthly expense realization document')
        verbose_name_plural = _('Monthly expense realization documents')


class YearlyExpenseDocument(ExpenseParsableDocument):
    timestamp = models.DateField(verbose_name=_('Datum obdelave podatkov'), null=True, blank=True)

    def __str__(self):
        return f'{self.municipality_year.financial_year.name}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.file:
            self.parse(
                parser=XLSXAppraBudget,
                model=YearlyExpense
            )

    class Meta:
        unique_together = ['municipality_year']
        verbose_name = _('Yearly expense document')
        verbose_name_plural = _('Yearly expense documents')


class Instructions(models.Model):
    model = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.CASCADE, verbose_name=_('Model'))
    list_instructions = MartorField(null=True, blank=True, verbose_name=_('Instructions for list of objects'))
    add_instructions = MartorField(null=True, blank=True, verbose_name=_('Instructions for adding object'))
    edit_instructions = MartorField(null=True, blank=True, verbose_name=_('Instructions for edit single object'))

    def __str__(self):
        if self.model:
            return f'{self.model}'
        else:
            return 'Landing'

    class Meta:
        verbose_name = _('Instructions')
        verbose_name_plural = _('Instructions')
