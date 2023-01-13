from django.contrib import admin, messages
from mptt.admin import MPTTModelAdmin

from django.utils.translation import gettext_lazy as _

from obcine.models import (PlannedExpense, MonthlyExpenseDocument, MonthlyExpense, MunicipalityFinancialYear,
    PlannedExpenseDocument, PlannedRevenueDocument, MonthlyRevenueDocument, PlannedRevenue,
    MonthlyRevenue)

import json

# Register your models here.

class LimitedAdmin(admin.ModelAdmin):
    exclude = ['organization', 'year']
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if not request.user.municipality:
            # return empty queryset if user has not municipality
            return qs.model.objects.none()
        return qs.filter(municipality=request.user.municipality)

    def message_user(self, *args):
        pass

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if ('revenuecategory' in request.resolver_match.route) or ('expensescategory' in request.resolver_match.route):
            pass
        else:
            messages.success(request, _("Changes are successful saved"))

    def get_inline_formsets(self, request, formsets, inline_instances, obj=None):
        """
        override inline formsets for rename add text
        """
        inline_formsets = super().get_inline_formsets(request, formsets, inline_instances, obj)

        data = [json.loads(inline_formset.inline_formset_data()) for inline_formset in inline_formsets]
        for item in data:
            item['options']['addText'] = 'Dodaj'

        for i, inline_formset in enumerate(inline_formsets):
            def inline_formset_data(data):
                return json.dumps(data)

            inline_formsets[i].inline_formset_data = inline_formset_data(data[i])
        return inline_formsets


class FinancialCategoryMPTTModelAdmin(MPTTModelAdmin):
    mptt_level_indent = 40
    list_display = ['name', 'code', 'level', 'amount', 'year']
    readonly_fields = ['document', 'year', 'amount', 'municipality']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('categories_children')


class RevenueDefinitionAdmin(MPTTModelAdmin):
    mptt_level_indent = 40
    list_display = ['name', 'code', 'level']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('categories_children')


class DocumentTabularInline(admin.TabularInline):
    exclude = ['municipality']


class BudgetDocumentInlineAdmin(DocumentTabularInline):
    model = PlannedExpenseDocument
    extra = 0


class MonthlyBudgetRealizationInlineAdmin(DocumentTabularInline):
    model = MonthlyExpenseDocument
    extra = 0


class RevenueDocumentInlineAdmin(DocumentTabularInline):
    model = PlannedRevenueDocument
    extra = 0


class RevenueBudgetRealizationInlineAdmin(DocumentTabularInline):
    model = MonthlyRevenueDocument
    extra = 0


class MunicipalityFinancialYearAdmin(admin.ModelAdmin):
    list_display = ['year']
    exclude = ['municipality', 'financial_year']
    inlines = [
        BudgetDocumentInlineAdmin,
        MonthlyBudgetRealizationInlineAdmin,
        RevenueDocumentInlineAdmin,
        RevenueBudgetRealizationInlineAdmin
    ]
    def year(self, obj):
        return obj.financial_year.name

    def save_formset(self, request, form, formset, change):
        """
        add municipality of user to each inline object
        """
        instances = formset.save(commit=False)
        for obj in formset.deleted_objects:
            obj.delete()
        for instance in instances:
            instance.municipality = request.user.municipality
            instance.save()
        formset.save_m2m()


class FinancialYearModelAdmin(admin.ModelAdmin):
    list_display = ['name']


class BudgetAdmin(FinancialCategoryMPTTModelAdmin):
    pass

class MonthlyBudgetRealizatioAdmin(FinancialCategoryMPTTModelAdmin):
    pass


class RevenueAdmin(admin.ModelAdmin):
    list_display = ['year', 'name', 'code', 'amount', 'status']
    readonly_fields = ['document', 'year', 'amount', 'municipality']

    def status(self, obj):
        if obj.definition:
            return 'OK'
        else:
            return 'Napaka pri izbiri konta'

class MonthlyRevenueRealizatioObcineAdmin(admin.ModelAdmin):
    list_display = ['year', 'month', 'name', 'code', 'amount', 'status']
    readonly_fields = ['document', 'year', 'amount', 'municipality']

    def status(self, obj):
        if obj.definition:
            return 'OK'
        else:
            return 'Napaka pri izbiri konta'

class AdminSite(admin.AdminSite):
    site_header = _('Nadzorna plošča')

admin_site = AdminSite(name='Nadzorna plošča')


admin_site.register(PlannedExpense, BudgetAdmin)
admin_site.register(MonthlyExpense, MonthlyBudgetRealizatioAdmin)


admin_site.register(PlannedRevenue, RevenueAdmin)
admin_site.register(MonthlyRevenue, MonthlyRevenueRealizatioObcineAdmin)

#admin_site.register(RevenueDefinition, RevenueDefinitionAdmin)
admin_site.register(MunicipalityFinancialYear, MunicipalityFinancialYearAdmin)
