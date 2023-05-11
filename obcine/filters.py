from django.contrib import admin
from obcine.models import FinancialYear
from django.utils.translation import gettext_lazy as _

class SimpleFinanceYearListFilter(admin.SimpleListFilter):
    title = _('By financial year')
    parameter_name = 'year'

    def lookups(self, request, model_admin):
        if request.user.is_superuser:
            years = FinancialYear.objects.all()
        else:
            years = FinancialYear.objects.all().order_by('-name')
        return (
            (year.id, year.name) for year in years
        )

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(year_id=self.value())
        else:
            # default filter by last name
            last_year = FinancialYear.objects.all().order_by('name').last()
            return queryset.filter(year=last_year)

    def choices(self, changelist):
        value = self.value()
        if not value:
            value = FinancialYear.objects.all().order_by('name').last().id
        for lookup, title in self.lookup_choices:
            yield {
                'selected': str(value) == str(lookup),
                'query_string': changelist.get_query_string({self.parameter_name: lookup}),
                'display': title,
            }
