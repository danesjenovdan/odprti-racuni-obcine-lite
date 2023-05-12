from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from mptt.admin import MPTTModelAdmin

from obcine.models import (PlannedExpense, MonthlyExpenseDocument, MonthlyExpense, Municipality,
    FinancialYear, PlannedExpenseDocument, RevenueDefinition, PlannedRevenueDocument, MonthlyRevenueDocument, PlannedRevenue,
    MonthlyRevenue, User, Task, YearlyExpenseDocument, YearlyRevenueDocument, YearlyExpense, YearlyRevenue,
    MunicipalityFinancialYear)


# Register your models here.


class UserAdmin(UserAdmin):
    model = User
    list_display = ['username', 'email', 'municipality']

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'municipality')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
    )

class FinancialCategoryMPTTModelAdmin(MPTTModelAdmin):
    mptt_level_indent = 40
    list_display = ['name', 'code', 'level', 'amount', 'year']

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
    exclude = ['municipality', 'year']

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


class YearlyRevenueDocumentInlineAdmin(DocumentTabularInline):
    model = YearlyRevenueDocument
    extra = 0

class YearlyBudgetRealizationInlineAdmin(DocumentTabularInline):
    model = YearlyExpenseDocument
    extra = 0


class MunicipalityModelAdmin(admin.ModelAdmin):
    list_display = ['name']


class FinancialYearModelAdmin(admin.ModelAdmin):
    list_display = ['name']


class BudgetAdmin(FinancialCategoryMPTTModelAdmin):
    list_filter = ['year', 'municipality']


class MonthlyBudgetRealizatioAdmin(FinancialCategoryMPTTModelAdmin):
    list_filter = ['year', 'municipality']


class YearlyBudgetAdmin(FinancialCategoryMPTTModelAdmin):
    list_filter = ['year', 'municipality']


class YearlyRevenueObcineAdmin(admin.ModelAdmin):
    list_display = ['year', 'name', 'code', 'amount', 'status']
    readonly_fields = ['document', 'year', 'amount', 'municipality']
    list_filter = ['municipality', 'year']

    def status(self, obj):
        if obj.definition:
            return 'OK'
        else:
            return 'Napaka pri izbiri konta'

class RevenueAdmin(admin.ModelAdmin):
    list_display = ['year', 'name', 'code', 'amount', 'status']
    list_filter = ['year', 'municipality']

    def status(self, obj):
        if obj.definition:
            return 'OK'
        else:
            return 'Napaka pri izbiri konta'
        

class TaskAdmin(admin.ModelAdmin):
    list_display = ['name']

class MonthlyRevenueRealizatioObcineAdmin(admin.ModelAdmin):
    list_display = ['year', 'month', 'name', 'code', 'amount', 'status']
    list_filter = ['year', 'municipality']

    def status(self, obj):
        if obj.definition:
            return 'OK'
        else:
            return 'Napaka pri izbiri konta'


class MunicipalityFinancialYearAdmin(admin.ModelAdmin):
    list_display = ['municipality', 'year', 'is_published']
    exclude = ['municipality', 'financial_year']
    list_filter = ['financial_year', 'municipality']
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

admin.site.register(User, UserAdmin)
admin.site.register(Task, TaskAdmin)

admin.site.register(PlannedExpense, BudgetAdmin)
admin.site.register(MonthlyExpense, MonthlyBudgetRealizatioAdmin)

admin.site.register(PlannedRevenue, RevenueAdmin)
admin.site.register(MonthlyRevenue, MonthlyRevenueRealizatioObcineAdmin)

admin.site.register(YearlyExpense, YearlyBudgetAdmin)
admin.site.register(YearlyRevenue, YearlyRevenueObcineAdmin)

admin.site.register(FinancialYear, FinancialYearModelAdmin)
admin.site.register(Municipality, MunicipalityModelAdmin)
admin.site.register(RevenueDefinition, RevenueDefinitionAdmin)

admin.site.register(MunicipalityFinancialYear, MunicipalityFinancialYearAdmin)
