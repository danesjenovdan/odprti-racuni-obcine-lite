from obcine.models import (PlannedExpense, MonthlyExpense, RevenueDefinition, PlannedRevenue, MonthlyRevenue,
    Municipality, FinancialYear)
from obcine.tree_utils import RevenueTreeBuilder, ExpanseTreeBuilder
from django.http import JsonResponse
from django.shortcuts import render

def get_year(year_id):
    if year_id:
        return FinancialYear.objects.get(id=year_id)
    else:
        return FinancialYear.objects.last()

# Create your views here.
def cut_off_funds(request, municipality_id, year_id=None):
    municipality = Municipality.objects.get(id=municipality_id)
    year = get_year(year_id)

    rtb = RevenueTreeBuilder(RevenueDefinition, municipality=municipality, financial_year=year)
    monthly_revenue = rtb.get_revenue_tree(MonthlyRevenue)
    planned_revenue = rtb.get_revenue_tree(PlannedRevenue)

    etb = ExpanseTreeBuilder(municipality=municipality, financial_year=year)
    monhtly_expenses = etb.get_expense_tree(MonthlyExpense)
    planned_expenses = etb.get_expense_tree(PlannedExpense)

    summary = {
        'planned_budget': sum([i['amount'] for i in planned_expenses.values()]),
        'planned_revenue': sum([i['amount'] for i in planned_revenue.values()]),
        'realized_budget': sum([i['amount'] for i in monhtly_expenses.values()]),
        'realized_revenue': sum([i['amount'] for i in monthly_revenue.values()]),
    }

    return render(
        request,
        'cut_off_funds.html',
        {
        'monthly_revenue': monthly_revenue,
        'planned_revenue': planned_revenue,
        'monhtly_expenses': monhtly_expenses,
        'planned_expenses': planned_expenses,
        'summary': summary
    })

def comparison_over_time(request, municipality_id):

    municipality = Municipality.objects.get(id=municipality_id)
    years = FinancialYear.objects.all()
    data = {}
    for year in years:
        etb = ExpanseTreeBuilder(municipality=municipality, financial_year=year)
        monhtly_expenses = etb.get_expense_tree(MonthlyExpense)
        data[year.name] = monhtly_expenses

    return render(
        request,
        'comparison_over_time.html',
        {'budget': data}
    )

def overview(request, municipality_id, year_id=None):
    municipality = Municipality.objects.get(id=municipality_id)
    year = get_year(year_id)

    rtb = RevenueTreeBuilder(RevenueDefinition, municipality=municipality, financial_year=year)
    monthly_revenue = rtb.get_revenue_tree(MonthlyRevenue)
    planned_revenue = rtb.get_revenue_tree(PlannedRevenue)

    etb = ExpanseTreeBuilder(municipality=municipality, financial_year=year)
    monhtly_expenses = etb.get_expense_tree(MonthlyExpense)
    planned_expenses = etb.get_expense_tree(PlannedExpense)

    summary = {
        'planned_budget': sum([i['amount'] for i in planned_expenses.values()]),
        'planned_revenue': sum([i['amount'] for i in planned_revenue.values()]),
        'realized_budget': sum([i['amount'] for i in monhtly_expenses.values()]),
        'realized_revenue': sum([i['amount'] for i in monthly_revenue.values()]),
    }

    print('summary', summary)

    return render(
        request,
        'overview.html',
        {
            'summary': summary
        }
    )

def budget(request, municipality_id, year_id=None):
    municipality = Municipality.objects.get(id=municipality_id)
    year = get_year(year_id)

    rtb = RevenueTreeBuilder(RevenueDefinition, municipality=municipality, financial_year=year)
    monthly_revenue = rtb.get_revenue_tree(MonthlyRevenue)
    planned_revenue = rtb.get_revenue_tree(PlannedRevenue)

    etb = ExpanseTreeBuilder(municipality=municipality, financial_year=year)
    monhtly_expenses = etb.get_expense_tree(MonthlyExpense)
    planned_expenses = etb.get_expense_tree(PlannedExpense)

    return render(
        request,
        '',
        {
            'monthly_revenue': monthly_revenue,
            'planned_revenue': planned_revenue,
            'monhtly_expenses': monhtly_expenses,
            'planned_expenses': planned_expenses,
        }
    )
