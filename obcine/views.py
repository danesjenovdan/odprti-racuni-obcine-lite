from django.shortcuts import render

from obcine.models import (
    FinancialYear,
    MonthlyExpense,
    MonthlyRevenue,
    Municipality,
    PlannedExpense,
    PlannedRevenue,
    RevenueDefinition,
    YearlyExpense,
    YearlyRevenue,
)
from obcine.tree_utils import ExpenseTreeBuilder, RevenueTreeBuilder


def get_year(year_id):
    if year_id:
        return FinancialYear.objects.get(id=year_id)
    else:
        return FinancialYear.objects.last()


def get_summary(municipality, year, summary_type="monthly"):
    rtb = RevenueTreeBuilder(
        RevenueDefinition,
        municipality=municipality,
        financial_year=year,
    )
    etb = ExpenseTreeBuilder(
        municipality=municipality,
        financial_year=year,
    )

    if summary_type == "monthly":
        planned_expenses = etb.get_expense_tree(PlannedExpense)
        planned_revenue = rtb.get_revenue_tree(PlannedRevenue)
        realized_expenses = etb.get_expense_tree(MonthlyExpense)
        realized_revenue = rtb.get_revenue_tree(MonthlyRevenue)

        summary = {
            "planned_expenses": sum([i["amount"] for i in planned_expenses]),
            "planned_revenue": sum([i["amount"] for i in planned_revenue]),
            "realized_expenses": sum([i["amount"] for i in realized_expenses]),
            "realized_revenue": sum([i["amount"] for i in realized_revenue]),
        }

    elif summary_type == "yearly":
        realized_expenses = etb.get_expense_tree(YearlyExpense)
        realized_revenue = rtb.get_revenue_tree(YearlyRevenue)

        summary = {
            "realized_expenses": sum([i["amount"] for i in realized_expenses]),
            "realized_revenue": sum([i["amount"] for i in realized_revenue]),
        }

    summary_keys = list(summary.keys())
    summary_max_value = max(summary.values())
    for key in summary_keys:
        summary[f"{key}_percentage"] = (
            summary[key] / summary_max_value if summary_max_value > 0 else 0
        )

    return summary


def overview(request, municipality_id, year_id=None):
    municipality = Municipality.objects.get(id=municipality_id)
    year = get_year(year_id)

    summary = get_summary(municipality, year, summary_type="monthly")

    return render(
        request,
        "overview.html",
        {
            "municipality": municipality,
            "year": year,
            "summary": summary,
        },
    )


def cut_of_funds(request, municipality_id, year_id=None):
    municipality = Municipality.objects.get(id=municipality_id)
    year = get_year(year_id)

    rtb = RevenueTreeBuilder(
        RevenueDefinition,
        municipality=municipality,
        financial_year=year,
    )
    etb = ExpenseTreeBuilder(
        municipality=municipality,
        financial_year=year,
    )

    if year.is_current():
        merged_tree_revenues = rtb.get_merged_revenue_tree(
            PlannedRevenue,
            MonthlyRevenue,
        )
        merged_tree_expenses = etb.get_merged_expense_tree(
            PlannedExpense,
            MonthlyExpense,
        )

        summary = get_summary(municipality, year, summary_type="monthly")

        revenue = {
            "planned": summary["planned_revenue"],
            "realized": summary["realized_revenue"],
            "name": "Celotni prihodki",
            "code": None,
            "children": merged_tree_revenues,
        }

        expenses = {
            "planned": summary["planned_expenses"],
            "realized": summary["realized_expenses"],
            "name": "Celotni odhodki",
            "code": None,
            "children": merged_tree_expenses,
        }

    else:
        realized_revenue = rtb.get_revenue_tree(YearlyRevenue)
        realized_expenses = etb.get_expense_tree(YearlyExpense)

        summary = get_summary(municipality, year, summary_type="yearly")

        revenue = {
            "realized": summary["realized_revenue"],
            "name": "Celotni prihodki",
            "code": None,
            "children": realized_revenue,
        }

        expenses = {
            "realized": summary["realized_expenses"],
            "name": "Celotni odhodki",
            "code": None,
            "children": realized_expenses,
        }

    return render(
        request,
        "cut_of_funds.html",
        {
            "years": FinancialYear.objects.all(),  # TODO: only show valid years for this municipality
            "municipality": municipality,
            "year": year,
            "summary": summary,
            "revenue": revenue,
            "expenses": expenses,
        },
    )


def comparison_over_time(request, municipality_id):
    municipality = Municipality.objects.get(id=municipality_id)
    years = FinancialYear.objects.all()

    budget_data = {}
    revenue_data = {}

    for year in years:
        etb = ExpenseTreeBuilder(
            municipality=municipality,
            financial_year=year,
        )
        rtb = RevenueTreeBuilder(
            RevenueDefinition,
            municipality=municipality,
            financial_year=year,
        )
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
        "comparison_over_time.html",
        {
            "budget": budget_data,
            "revenue": revenue_data,
        },
    )
