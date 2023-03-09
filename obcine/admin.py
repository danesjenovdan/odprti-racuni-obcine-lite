from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from mptt.admin import MPTTModelAdmin

from obcine.models import (PlannedExpense, MonthlyExpenseDocument, MonthlyExpense, Municipality,
    FinancialYear, PlannedExpenseDocument, RevenueDefinition, PlannedRevenueDocument, MonthlyRevenueDocument, PlannedRevenue,
    MonthlyRevenue, User, Task)

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


class BudgetDocumentInlineAdmin(admin.TabularInline):
    model = PlannedExpenseDocument
    extra = 0


class MonthlyBudgetRealizationInlineAdmin(admin.TabularInline):
    model = MonthlyExpenseDocument
    extra = 0


class RevenueDocumentInlineAdmin(admin.TabularInline):
    model = PlannedRevenueDocument
    extra = 0


class RevenueBudgetRealizationInlineAdmin(admin.TabularInline):
    model = MonthlyRevenueDocument
    extra = 0


class MunicipalityModelAdmin(admin.ModelAdmin):
    list_display = ['name']

    inlines = [
        BudgetDocumentInlineAdmin,
        MonthlyBudgetRealizationInlineAdmin,
        RevenueDocumentInlineAdmin,
        RevenueBudgetRealizationInlineAdmin
    ]


class FinancialYearModelAdmin(admin.ModelAdmin):
    list_display = ['name']


class BudgetAdmin(FinancialCategoryMPTTModelAdmin):
    pass

class MonthlyBudgetRealizatioAdmin(FinancialCategoryMPTTModelAdmin):
    pass


class RevenueAdmin(admin.ModelAdmin):
    list_display = ['year', 'name', 'code', 'amount', 'status']

    def status(self, obj):
        if obj.definition:
            return 'OK'
        else:
            return 'Napaka pri izbiri konta'
        

class TaskAdmin(admin.ModelAdmin):
    list_display = ['name']

class MonthlyRevenueRealizatioObcineAdmin(admin.ModelAdmin):
    list_display = ['year', 'month', 'name', 'code', 'amount', 'status']

    def status(self, obj):
        if obj.definition:
            return 'OK'
        else:
            return 'Napaka pri izbiri konta'

admin.site.register(User, UserAdmin)
admin.site.register(Task, TaskAdmin)

admin.site.register(PlannedExpense, BudgetAdmin)
admin.site.register(MonthlyExpense, MonthlyBudgetRealizatioAdmin)

admin.site.register(PlannedRevenue, RevenueAdmin)
admin.site.register(MonthlyRevenue, MonthlyRevenueRealizatioObcineAdmin)

admin.site.register(FinancialYear, FinancialYearModelAdmin)
admin.site.register(Municipality, MunicipalityModelAdmin)
admin.site.register(RevenueDefinition, RevenueDefinitionAdmin)
