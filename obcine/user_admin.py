from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import NoReverseMatch, reverse
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
from django.apps import apps
from django.utils.text import capfirst

from obcine.models import (PlannedExpense, MonthlyExpenseDocument, MonthlyExpense, MunicipalityFinancialYear,
    PlannedExpenseDocument, PlannedRevenueDocument, MonthlyRevenueDocument, PlannedRevenue, YearlyExpense,
    MonthlyRevenue, YearlyRevenue, YearlyRevenueDocument, YearlyExpenseDocument, Municipality, Instructions)
from obcine.filters import SimpleFinanceYearListFilter


import json

from mptt.admin import MPTTModelAdmin

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


class FinancialCategoryMPTTModelAdmin(MPTTModelAdmin, LimitedAdmin):
    mptt_level_indent = 40
    list_display = ['name', 'code', 'level', 'amount', 'year']
    readonly_fields = ['document', 'year', 'amount', 'municipality']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('categories_children')


class RevenueDefinitionAdmin(MPTTModelAdmin, LimitedAdmin):
    mptt_level_indent = 40
    list_display = ['name', 'code', 'level']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('categories_children')


class DocumentTabularInline(admin.TabularInline):
    exclude = ['municipality', 'year']


class BudgetDocumentInlineAdmin(DocumentTabularInline):
    model = PlannedExpenseDocument
    extra = 0


class MonthlyBudgetRealizationInlineAdmin(DocumentTabularInline):
    model = MonthlyExpenseDocument
    extra = 0


class YearlyBudgetRealizationInlineAdmin(DocumentTabularInline):
    model = YearlyExpenseDocument
    extra = 0


class RevenueDocumentInlineAdmin(DocumentTabularInline):
    model = PlannedRevenueDocument
    extra = 0


class YearlyRevenueDocumentInlineAdmin(DocumentTabularInline):
    model = YearlyRevenueDocument
    extra = 0


class RevenueBudgetRealizationInlineAdmin(DocumentTabularInline):
    model = MonthlyRevenueDocument
    extra = 0


class MunicipalityFinancialYearAdmin(LimitedAdmin):
    list_display = ['year', 'is_published']
    exclude = ['municipality', 'financial_year']
    fields = ['budget_date', 'budget_type', 'is_published', 'page_url']
    readonly_fields = ['page_url']
    inlines = [
        BudgetDocumentInlineAdmin,
        MonthlyBudgetRealizationInlineAdmin,
        YearlyBudgetRealizationInlineAdmin,
        RevenueDocumentInlineAdmin,
        RevenueBudgetRealizationInlineAdmin,
        YearlyRevenueDocumentInlineAdmin
    ]
    def year(self, obj):
        return obj.financial_year.name

    def page_url(self, obj):
        return mark_safe(f'<a href="/pregled/{obj.municipality.id}/" target="_blank">Povezava do spletnega mesta</a>')


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

    page_url.allow_tags = True
    page_url.short_description = _("Povezava")


class FinancialYearModelAdmin(admin.ModelAdmin):
    list_display = ['name']


class BudgetAdmin(FinancialCategoryMPTTModelAdmin):
    list_filter = [SimpleFinanceYearListFilter]


class MonthlyBudgetRealizatioAdmin(FinancialCategoryMPTTModelAdmin):
    list_filter = [SimpleFinanceYearListFilter]


class YearlyBudgetAdmin(FinancialCategoryMPTTModelAdmin):
    list_filter = [SimpleFinanceYearListFilter]


class RevenueAdmin(LimitedAdmin):
    list_display = ['year', 'name', 'code', 'amount', 'status']
    readonly_fields = ['document', 'year', 'amount', 'municipality']
    list_filter = [SimpleFinanceYearListFilter]

    def status(self, obj):
        if obj.definition:
            return 'OK'
        else:
            return 'Napaka pri izbiri konta'


class YearlyRevenueObcineAdmin(LimitedAdmin):
    list_display = ['year', 'name', 'code', 'amount', 'status']
    readonly_fields = ['document', 'year', 'amount', 'municipality']
    list_filter = [SimpleFinanceYearListFilter]

    def status(self, obj):
        if obj.definition:
            return 'OK'
        else:
            return 'Napaka pri izbiri konta'

class MonthlyRevenueRealizatioObcineAdmin(LimitedAdmin):
    list_display = ['year', 'name', 'code', 'amount', 'status']
    readonly_fields = ['document', 'year', 'amount', 'municipality']
    list_filter = [SimpleFinanceYearListFilter]

    def status(self, obj):
        if obj.definition:
            return 'OK'
        else:
            return 'Napaka pri izbiri konta'


class MunicipalityModelAdmin(admin.ModelAdmin):
    list_display = ['name']

    def response_change(self, request, obj):
        return redirect(f'/obcine-admin/obcine/municipality/{obj.id}/change/')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.municipality or request.user.is_superuser:
            return qs
        return qs.filter(id=request.user.municipality.id)


class AdminSite(admin.AdminSite):
    site_header = _('Nadzorna plošča')
    site_title = _('Nadzorna plošča')
    index_title = _('Nadzorna plošča')
    site_url = None

    def each_context(self, request):
        url_attrs = []
        preview = ''

        url_name = request.resolver_match.url_name
        url_attrs = url_name.split('_')

        context = super().each_context(request)

        # insert instructions
        instructions = ''
        if url_attrs[0] == 'login':
            pass
        elif url_attrs[0] == 'logout':
            pass
        elif len(url_attrs) == 1:
            instructions = Instructions.objects.filter(model=None).first()
            if instructions and instructions.list_instructions:
                instructions = instructions.list_instructions
            else:
                instructions = ''
        elif len(url_attrs) == 3:
            instructions = Instructions.objects.filter(
                model__model__iexact=url_attrs[1]
            )
            if instructions:
                if url_attrs[2] == 'change':
                    instructions = instructions[0].edit_instructions
                elif url_attrs[2] == 'add':
                    instructions = instructions[0].add_instructions
                else:
                    instructions = instructions[0].list_instructions
            else:
                instructions = ''

        context.update({
            'instructions': instructions,
            'preview': preview
        })
        return context

    def get_app_list(self, request, app_label=None):
        app_list = list(self._build_app_dict(request, app_label).values())
        try:
            user_municipality_id = request.user.municipality_id
            self.site_url = reverse('overview', kwargs={'municipality_id': user_municipality_id})
        except:
            pass


        # Sort the models alphabetically within each app.
        for app in app_list:
            for idx, model in enumerate(app['models']):
                # add id of users municipality to municipality url
                if model['object_name'] == 'Municipality':
                    model['admin_url'] = model['admin_url'] + str(user_municipality_id)
            #print(app['app_url'])

        return app_list

admin_site = AdminSite(name='obcine-admin')

admin_site.register(MunicipalityFinancialYear, MunicipalityFinancialYearAdmin)

# admin_site.register(PlannedExpense, BudgetAdmin)
# admin_site.register(MonthlyExpense, MonthlyBudgetRealizatioAdmin)
# admin_site.register(YearlyExpense, YearlyBudgetAdmin)

# admin_site.register(PlannedRevenue, RevenueAdmin)
# admin_site.register(MonthlyRevenue, MonthlyRevenueRealizatioObcineAdmin)
# admin_site.register(YearlyRevenue, YearlyRevenueObcineAdmin)

admin_site.register(Municipality, MunicipalityModelAdmin)

#admin_site.register(RevenueDefinition, RevenueDefinitionAdmin)
