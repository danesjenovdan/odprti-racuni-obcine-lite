from obcine.models import (PlannedExpense, MonthlyExpense, RevenueDefinition, PlannedRevenue, MonthlyRevenue,
    Municipality, FinancialYear, YearlyRevenue, YearlyExpense)
from obcine.tree_utils import RevenueTreeBuilder, ExpanseTreeBuilder
from django.http import JsonResponse
from django.shortcuts import render

def get_year(year_id):
    if year_id:
        return FinancialYear.objects.get(id=year_id)
    else:
        return FinancialYear.objects.last()

def overview(request, municipality_id, year_id=None):
    municipality = Municipality.objects.get(id=municipality_id)
    year = get_year(year_id)

    rtb = RevenueTreeBuilder(RevenueDefinition, municipality=municipality, financial_year=year)
    monthly_revenue = rtb.get_revenue_tree(MonthlyRevenue)
    planned_revenue = rtb.get_revenue_tree(PlannedRevenue)

    etb = ExpanseTreeBuilder(municipality=municipality, financial_year=year)
    monhtly_expenses = etb.get_expense_tree(MonthlyExpense)
    planned_expenses = etb.get_expense_tree(PlannedExpense)

    print(type(monthly_revenue))
    print(type(planned_revenue))
    print(type(monhtly_expenses))
    print(type(planned_expenses))

    summary = {
        'planned_budget': sum([i['amount'] for i in planned_expenses]),
        'planned_revenue': sum([i['amount'] for i in planned_revenue]),
        'realized_budget': sum([i['amount'] for i in monhtly_expenses]),
        'realized_revenue': sum([i['amount'] for i in monthly_revenue]),
    }

    print('summary', summary)

    return render(
        request,
        'overview.html',
        {
            'summary': summary
        }
    )

def cut_off_funds(request, municipality_id, year_id=None,):
    municipality = Municipality.objects.get(id=municipality_id)
    year = get_year(year_id)

    rtb = RevenueTreeBuilder(RevenueDefinition, municipality=municipality, financial_year=year)
    etb = ExpanseTreeBuilder(municipality=municipality, financial_year=year)

    if year.is_current():
        # create data strucutre for current year
        monthly_revenue = rtb.get_revenue_tree(MonthlyRevenue)
        planned_revenue = rtb.get_revenue_tree(PlannedRevenue)

        monhtly_expenses = etb.get_expense_tree(MonthlyExpense)
        planned_expenses = etb.get_expense_tree(PlannedExpense)

        summary = {
            'planned_budget': sum([i['amount'] for i in planned_expenses]),
            'planned_revenue': sum([i['amount'] for i in planned_revenue]),
            'realized_budget': sum([i['amount'] for i in monhtly_expenses]),
            'realized_revenue': sum([i['amount'] for i in monthly_revenue]),
        }

        merged_tree_reveues = rtb.get_merged_revenue_tree(PlannedRevenue, MonthlyRevenue)
        merged_tree_expenses = etb.get_merged_expanse_tree(PlannedExpense, MonthlyExpense)

        revenues = {
            'planned': summary['planned_revenue'],
            'realized': summary['realized_revenue'],
            'name': 'Celotni prihodki',
            'code': None,
            'children': merged_tree_reveues
        }

        expenses = {
            'planned': summary['planned_budget'],
            'realized': summary['realized_budget'],
            'name': 'Celotni odhodki',
            'code': None,
            'children': merged_tree_expenses
        }

    else:
        # create data structure for past years
        yearly_revenue = rtb.get_revenue_tree(YearlyRevenue)
        yearly_expenses = etb.get_expense_tree(YearlyExpense)

        summary = {
            'yearly_revenue': sum([i['amount'] for i in yearly_revenue]),
            'yearly_expense': sum([i['amount'] for i in yearly_expenses]),
        }

        revenues = {
            'yearly': summary['yearly_revenue'],
            'name': 'Celotni prihodki',
            'code': None,
            'children': yearly_revenue
        }

        expenses = {
            'yearly': summary['yearly_expense'],
            'name': 'Celotni odhodki',
            'code': None,
            'children': yearly_expenses
        }

    return render(
        request,
        'cut_off_funds.html',
        {
        'year': year,
        'revenues': revenues,
        'expenses': expenses,
        'summary': summary
    })

def comparison_over_time(request, municipality_id):

    municipality = Municipality.objects.get(id=municipality_id)
    years = FinancialYear.objects.all()
    budget_data = {}
    revenue_data = {}
    for year in years:
        etb = ExpanseTreeBuilder(municipality=municipality, financial_year=year)
        rtb = RevenueTreeBuilder(RevenueDefinition, municipality=municipality, financial_year=year)
        if year.is_current:
            expenses = etb.get_expense_tree(MonthlyExpense)
            revenue = rtb.get_revenue_tree(MonthlyRevenue)
        else:
            expenses = etb.get_expense_tree(YearlyExpense)
            revenue = rtb.get_revenue_tree(YearlyRevenue)
        budget_data[year.name] = expenses
        revenue_data[year.name] = revenue

    return render(
        request,
        'comparison_over_time.html',
        {
            'budget': budget_data,
            'revenue': revenue_data
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
