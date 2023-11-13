from django.contrib import admin
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _
from mptt.admin import MPTTModelAdmin

from obcine.models import (PlannedExpense, MonthlyExpenseDocument, MonthlyExpense, Municipality,
    FinancialYear, PlannedExpenseDocument, RevenueDefinition, PlannedRevenueDocument, MonthlyRevenueDocument, PlannedRevenue,
    MonthlyRevenue, User, Task, YearlyExpenseDocument, YearlyRevenueDocument, YearlyExpense, YearlyRevenue,
    MunicipalityFinancialYear, Instructions)

# Register your models here.


class UserAdmin(UserAdmin):
    model = User
    list_display = ['username', 'email', 'municipality']

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'municipality')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups'),
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

    search_fields = ['name', 'code']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('categories_children')


class DocumentTabularInline(admin.TabularInline):
    exclude = ['municipality', 'year']

class ExpenseDocumentTabularInline(DocumentTabularInline):
    pass

class RevenueTabularInline(DocumentTabularInline):
    pass


class BudgetDocumentInlineAdmin(ExpenseDocumentTabularInline):
    model = PlannedExpenseDocument
    extra = 0


class MonthlyBudgetRealizationInlineAdmin(ExpenseDocumentTabularInline):
    model = MonthlyExpenseDocument
    extra = 0


class YearlyBudgetRealizationInlineAdmin(ExpenseDocumentTabularInline):
    model = YearlyExpenseDocument
    extra = 0


class RevenueDocumentInlineAdmin(RevenueTabularInline):
    model = PlannedRevenueDocument
    extra = 0


class RevenueRealizationInlineAdmin(RevenueTabularInline):
    model = MonthlyRevenueDocument
    extra = 0


class YearlyRevenueDocumentInlineAdmin(RevenueTabularInline):
    model = YearlyRevenueDocument
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
    autocomplete_fields = ['definition']

    search_fields = ['name', 'code']

    def status(self, obj):
        if obj.definition:
            return 'OK'
        else:
            return 'Napaka pri izbiri konta'
        

class TaskAdmin(admin.ModelAdmin):
    list_display = ['name']

class MonthlyRevenueRealizatioObcineAdmin(admin.ModelAdmin):
    list_display = ['year', 'name', 'code', 'amount', 'status']
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
        RevenueRealizationInlineAdmin,
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

class InstructionsAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        # TODO
        # if Instructions.objects.filter(model=obj.model):
        #     messages.add_message(request, messages.ERROR, 'Instrucations for this model alredy exists')
        # else:
        super().save_model(request, obj, form, change)

class SuperAdminSite(admin.AdminSite):
    site_header = 'Odprti računi občine'
    site_title = 'Odprti računi občine'
    index_title = 'Odprti računi občine'

    def has_permission(self, request):
        """
        Prevent municipality users to login to superadmin site
        """
        return request.user.is_superuser


superadmin = SuperAdminSite(name='admin')

superadmin.register(User, UserAdmin)
superadmin.register(Task, TaskAdmin)

superadmin.register(Group, GroupAdmin)

superadmin.register(PlannedExpense, BudgetAdmin)
superadmin.register(MonthlyExpense, MonthlyBudgetRealizatioAdmin)

superadmin.register(PlannedRevenue, RevenueAdmin)
superadmin.register(MonthlyRevenue, MonthlyRevenueRealizatioObcineAdmin)

superadmin.register(YearlyExpense, YearlyBudgetAdmin)
superadmin.register(YearlyRevenue, YearlyRevenueObcineAdmin)

superadmin.register(FinancialYear, FinancialYearModelAdmin)
superadmin.register(Municipality, MunicipalityModelAdmin)
superadmin.register(RevenueDefinition, RevenueDefinitionAdmin)

superadmin.register(MunicipalityFinancialYear, MunicipalityFinancialYearAdmin)

superadmin.register(Instructions, InstructionsAdmin)
