from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from django.conf import settings
from importlib import import_module

from mptt.models import MPTTModel, TreeForeignKey

from datetime import datetime

from obcine.parse_utils import XLSXAppraBudget, XLSXAppraRevenue, download_file


def document_size_validator(value): # add this to some file where you can import it from
    limit = 10 * 1024 * 1024
    if value.size > limit:
        raise ValidationError('Datoteka je prevelika. Največja možna velikost je 10 MB.')

def image_validator(image):
    limit = 1 * 1024 * 1024
    if image.size > limit:
        raise ValidationError('Slika je prevelika. Največja možna velikost je 1 MB.')

def validate_image_extension(value):
    ext = os.path.splitext(value.name)[1]  # [0] returns path+filename
    valid_extensions = ['.jpg', '.jpeg', '.png']
    if not ext.lower() in valid_extensions:
        raise ValidationError('Format slike ni veljaven ali pa je slika poškodovana.')

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
            month = data.get('month', None)
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
                    definiton_model=definiton_model,
                    month=month
                )
            else:
                parser = parser_class(
                    document,
                    model=models_class,
                    definiton_model=None,
                    month=month
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
        validators=[
            FileExtensionValidator(allowed_extensions=['xlsx']),
            document_size_validator
        ]
    )

    def parse(self, parser, model, definition=None, month=None):
        if definition:
            definition = definition.__name__
        Task(
            name='Parse xls',
            payload={
                'model': f'{model.__name__}',
                'parser': f'{parser.__name__}',
                'definition': f'{definition}',
                'month': f'{month}',
                'pk': self.id,
                'self': f'{self.__class__.__name__}',
            }
        ).save()
        # parser = parser(self, model, definition, month)
        # if settings.ENABLE_S3:
        #     image_path = download_file(self.file.url, self.file.name)
        #     parser.parse_file(file_path=image_path)
        # else:
        #     parser.parse_file(file_path=self.file.path)

    class Meta:
        abstract = True


class Municipality(Timestampable):
    name = models.TextField(verbose_name=_('Nemo of municipality'))
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
        return str(datetime.now().year) == self.name

    class Meta:
        verbose_name = _('Financial year')
        verbose_name_plural = _('Financial years')
        ordering = ['name']

class MunicipalityFinancialYear(Timestampable):
    financial_year = models.ForeignKey('FinancialYear', related_name='municipalityfinancialyears', on_delete=models.PROTECT)
    municipality = models.ForeignKey('Municipality', related_name='municipalityfinancialyears', on_delete=models.PROTECT)
    adoption_date_of_budget = models.DateField(verbose_name=_('Datum sprejetja proračuna'), null=True, blank=True)
    rebalans_date_of_budget = models.DateField(verbose_name=_('Datum rebalansa proračuna'), null=True, blank=True)
    is_published = models.BooleanField(default=False)

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
    month = models.IntegerField(choices=Months.choices, verbose_name=_('Month'))
    document = models.ForeignKey('MonthlyRevenueDocument', on_delete=models.CASCADE)


class PlannedRevenueDocument(ParsableDocument):
    def __str__(self):
        return f'{self.municipality_year.financial_year.name}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # delete data if file reupload
        self.children.all().delete()
        self.parse(
            parser=XLSXAppraRevenue,
            model=PlannedRevenue,
            definition=RevenueDefinition
        )

    class Meta:
        unique_together = ['municipality_year']
        verbose_name = _('Planned revenue document')
        verbose_name_plural = _('Planned revenue documents')


class YearlyRevenueDocument(ParsableDocument):
    def __str__(self):
        return f'{self.municipality_year.financial_year.name}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.parse(
            parser=XLSXAppraRevenue,
            model=YearlyRevenue,
            definition=RevenueDefinition
        )

    class Meta:
        unique_together = ['municipality_year']
        verbose_name = _('Yearly revenue document')
        verbose_name_plural = _('Yearly revenue documents')


class MonthlyRevenueDocument(ParsableDocument):
    month = models.IntegerField(choices=Months.choices, verbose_name=_('Month'))

    def __str__(self):
        return f'{self.municipality_year.financial_year.name}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.parse(
            parser=XLSXAppraRevenue,
            model=MonthlyRevenue,
            definition=RevenueDefinition,
            month=self.month
        )

    class Meta:
        unique_together = ['municipality_year', 'month']
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
    month = models.IntegerField(choices=Months.choices, verbose_name=_('Month'))
    document = models.ForeignKey('MonthlyExpenseDocument', on_delete=models.CASCADE)
    class Meta:
        verbose_name = _('Monthly expense')
        verbose_name_plural = _('Monthly expense')


class PlannedExpenseDocument(ParsableDocument):
    def __str__(self):
        return f'{self.municipality_year.financial_year.name}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # delete data if file reupload
        self.children.all().delete()
        self.parse(
            parser=XLSXAppraBudget,
            model=PlannedExpense,
        )

    class Meta:
        unique_together = ['municipality_year']
        verbose_name = _('Planned expense document')
        verbose_name_plural = _('Planned expense documents')


class MonthlyExpenseDocument(ParsableDocument):
    month = models.IntegerField(choices=Months.choices, verbose_name=_('Month'))

    def __str__(self):
        return f'{self.municipality_year.financial_year.name}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.parse(
            parser=XLSXAppraBudget,
            model=MonthlyExpense,
            month=self.month
        )

    class Meta:
        unique_together = ['municipality_year', 'month']
        verbose_name = _('Monthly expense realization document')
        verbose_name_plural = _('Monthly expense realization documents')


class YearlyExpenseDocument(ParsableDocument):
    def __str__(self):
        return f'{self.municipality_year.financial_year.name}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.parse(
            parser=XLSXAppraBudget,
            model=YearlyExpense
        )

    class Meta:
        unique_together = ['municipality_year']
        verbose_name = _('Yearly expense document')
        verbose_name_plural = _('Yearly expense documents')
