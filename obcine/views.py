from obcine.models import (PlannedExpense, MonthlyExpense, RevenueDefinition, PlannedRevenue, MonthlyRevenue,
    Municipality, FinancialYear, YearlyRevenue, YearlyExpense)
from obcine.tree_utils import RevenueTreeBuilder, ExpenseTreeBuilder
from django.http import JsonResponse
from django.shortcuts import render


def get_year(year_id):
    if year_id:
        return FinancialYear.objects.get(id=year_id)
    else:
        return FinancialYear.objects.last()


def get_summary(municipality, year, summary_type="monthly"):
    rtb = RevenueTreeBuilder(RevenueDefinition, municipality=municipality, financial_year=year)
    etb = ExpenseTreeBuilder(municipality=municipality, financial_year=year)

    if summary_type == "monthly":
        planned_expenses = etb.get_expense_tree(PlannedExpense)
        planned_revenue = rtb.get_revenue_tree(PlannedRevenue)
        monthly_expenses = etb.get_expense_tree(MonthlyExpense)
        monthly_revenue = rtb.get_revenue_tree(MonthlyRevenue)

        summary = {
            'planned_expenses': sum([i['amount'] for i in planned_expenses]),
            'planned_revenue': sum([i['amount'] for i in planned_revenue]),
            'realized_expenses': sum([i['amount'] for i in monthly_expenses]),
            'realized_revenue': sum([i['amount'] for i in monthly_revenue]),
        }

        summary_max_value = max(summary.values())
        if summary_max_value > 0:
            summary['planned_expenses_percentage'] = summary['planned_expenses'] / summary_max_value
            summary['planned_revenue_percentage'] = summary['planned_revenue'] / summary_max_value
            summary['realized_expenses_percentage'] = summary['realized_expenses'] / summary['planned_expenses']
            summary['realized_revenue_percentage'] = summary['realized_revenue'] / summary['planned_revenue']

    elif summary_type == "yearly":
        yearly_expenses = etb.get_expense_tree(YearlyExpense)
        yearly_revenue = rtb.get_revenue_tree(YearlyRevenue)

        summary = {
            'yearly_expenses': sum([i['amount'] for i in yearly_expenses]),
            'yearly_revenue': sum([i['amount'] for i in yearly_revenue]),
        }

        summary_max_value = max(summary.values())
        if summary_max_value > 0:
            summary['yearly_expenses_percentage'] = summary['yearly_expenses'] / summary_max_value
            summary['yearly_revenue_percentage'] = summary['yearly_revenue'] / summary_max_value

    return summary


def overview(request, municipality_id, year_id=None):
    municipality = Municipality.objects.get(id=municipality_id)
    year = get_year(year_id)

    summary = get_summary(municipality, year, summary_type="monthly")

    return render(request, 'overview.html', {
        'municipality': municipality,
        'year': year,
        'summary': summary,
    })


def cut_of_funds(request, municipality_id, year_id=None):
    municipality = Municipality.objects.get(id=municipality_id)
    year = get_year(year_id)

    rtb = RevenueTreeBuilder(RevenueDefinition, municipality=municipality, financial_year=year)
    etb = ExpenseTreeBuilder(municipality=municipality, financial_year=year)

    if year.is_current():
        merged_tree_reveues = rtb.get_merged_revenue_tree(PlannedRevenue, MonthlyRevenue)
        merged_tree_expenses = etb.get_merged_expense_tree(PlannedExpense, MonthlyExpense)

        summary = get_summary(municipality, year, summary_type="monthly")

        revenue = {
            'planned': summary['planned_revenue'],
            'realized': summary['realized_revenue'],
            'name': 'Celotni prihodki',
            'code': None,
            'children': merged_tree_reveues
        }

        expenses = {
            'planned': summary['planned_expenses'],
            'realized': summary['realized_expenses'],
            'name': 'Celotni odhodki',
            'code': None,
            'children': merged_tree_expenses
        }

    else:
        yearly_revenue = rtb.get_revenue_tree(YearlyRevenue)
        yearly_expenses = etb.get_expense_tree(YearlyExpense)

        summary = get_summary(municipality, year, summary_type="yearly")

        revenue = {
            'yearly': summary['yearly_revenue'],
            'name': 'Celotni prihodki',
            'code': None,
            'children': yearly_revenue
        }

        expenses = {
            'yearly': summary['yearly_expenses'],
            'name': 'Celotni odhodki',
            'code': None,
            'children': yearly_expenses
        }

    return render(request, 'cut_of_funds.html', {
        'years': FinancialYear.objects.all(), # TODO: only show valid years for this municipality
        'municipality': municipality,
        'year': year,
        'summary': summary,
        'revenue': revenue,
        'expenses': expenses,
    })

def comparison_over_time(request, municipality_id):
    municipality = Municipality.objects.get(id=municipality_id)
    years = FinancialYear.objects.all()
    budget_data = {}
    revenue_data = {}
    for year in years:
        etb = ExpenseTreeBuilder(municipality=municipality, financial_year=year)
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

    etb = ExpenseTreeBuilder(municipality=municipality, financial_year=year)
    monthly_expenses = etb.get_expense_tree(MonthlyExpense)
    planned_expenses = etb.get_expense_tree(PlannedExpense)

    return render(
        request,
        '',
        {
            'monthly_revenue': monthly_revenue,
            'planned_revenue': planned_revenue,
            'monthly_expenses': monthly_expenses,
            'planned_expenses': planned_expenses,
        }
    )
