from obcine.models import (PlannedExpense, MonthlyExpense, RevenueDefinition, PlannedRevenue, MonthlyRevenue,
    Municipality, FinancialYear)
from obcine.tree_utils import RevenueTreeBuilder, ExpanseTreeBuilder
from django.http import JsonResponse


# Create your views here.
def cut_off_funds(request, municipality_id, year_id):
    municipality = Municipality.objects.get(id=municipality_id)
    year = FinancialYear.objects.get(id=year_id)

    rtb = RevenueTreeBuilder(RevenueDefinition, municipality=municipality, financial_year=year)
    monthly_revenue = rtb.get_revenue_tree(MonthlyRevenue)
    planned_revenue = rtb.get_revenue_tree(PlannedRevenue)

    etb = ExpanseTreeBuilder(municipality=municipality, financial_year=year)
    monhtly_expenses = etb.get_expense_tree(MonthlyExpense)
    planned_expenses = etb.get_expense_tree(PlannedExpense)

    return JsonResponse({
        'monthly_revenue': monthly_revenue,
        'planned_revenue': planned_revenue,
        'monhtly_expenses': monhtly_expenses,
        'planned_expenses': planned_expenses,
    })

def over_the_years(request, municipality_id, year_id):

    budget_roots = MonthlyExpense.objects.filter(
        municipality_id=municipality_id,
        year_id=year_id,
    )

    budget_data = []
    for root in budget_roots:
        budget_data.append(root.get_json_tree())

    return JsonResponse({'budget': budget_data})

def budet_flow(request, municipality_id, year_id):
    municipality = Municipality.objects.get(id=municipality_id)
    year = FinancialYear.objects.get(id=year_id)

    rtb = RevenueTreeBuilder(RevenueDefinition, municipality=municipality, financial_year=year)
    monthly_revenue = rtb.get_revenue_tree(MonthlyRevenue)
    planned_revenue = rtb.get_revenue_tree(PlannedRevenue)

    etb = ExpanseTreeBuilder(municipality=municipality, financial_year=year)
    monhtly_expenses = etb.get_expense_tree(MonthlyExpense)
    planned_expenses = etb.get_expense_tree(PlannedExpense)

    return JsonResponse({
        'monthly_revenue': monthly_revenue,
        'planned_revenue': planned_revenue,
        'monhtly_expenses': monhtly_expenses,
        'planned_expenses': planned_expenses,
    })


