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


def get_tree_type(query_dict):
    return "expenses" if query_dict.get("type", "") == "expenses" else "revenue"


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


def get_revenue_tree(municipality, year, summary):
    rtb = RevenueTreeBuilder(
        RevenueDefinition,
        municipality=municipality,
        financial_year=year,
    )

    if year.is_current():
        merged_tree_revenues = rtb.get_merged_revenue_tree(
            PlannedRevenue,
            MonthlyRevenue,
        )

        return {
            "planned": summary["planned_revenue"],
            "realized": summary["realized_revenue"],
            "name": "Celotni prihodki",
            "code": None,
            "children": merged_tree_revenues,
        }

    else:
        realized_revenue = rtb.get_revenue_tree(YearlyRevenue)

        return {
            "realized": summary["realized_revenue"],
            "name": "Celotni prihodki",
            "code": None,
            "children": realized_revenue,
        }


def get_expense_tree(municipality, year, summary):
    etb = ExpenseTreeBuilder(
        municipality=municipality,
        financial_year=year,
    )

    if year.is_current():
        merged_tree_expenses = etb.get_merged_expense_tree(
            PlannedExpense,
            MonthlyExpense,
        )

        return {
            "planned": summary["planned_expenses"],
            "realized": summary["realized_expenses"],
            "name": "Celotni odhodki",
            "code": None,
            "children": merged_tree_expenses,
        }

    else:
        realized_expenses = etb.get_expense_tree(YearlyExpense)

        return {
            "realized": summary["realized_expenses"],
            "name": "Celotni odhodki",
            "code": None,
            "children": realized_expenses,
        }


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
    tree_type = get_tree_type(request.GET)

    summary_type = "monthly" if year.is_current() else "yearly"
    summary = get_summary(municipality, year, summary_type=summary_type)

    revenue = get_revenue_tree(municipality, year, summary)
    expenses = get_expense_tree(municipality, year, summary)

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
            "tree_type": tree_type,
        },
    )


def cut_of_funds_table(request, municipality_id, year_id=None):
    municipality = Municipality.objects.get(id=municipality_id)
    year = get_year(year_id)
    tree_type = get_tree_type(request.GET)

    summary_type = "monthly" if year.is_current() else "yearly"
    summary = get_summary(municipality, year, summary_type=summary_type)

    tree_data = []
    parent_code = None

    if tree_type == "expenses":
        tree_data = get_expense_tree(municipality, year, summary)
    else:
        tree_data = get_revenue_tree(municipality, year, summary)

    def find_code(code, parent, node):
        if node["code"] == code:
            return node, parent["code"]

        if children := node.get("children", []):
            for child in children:
                found, parent_code = find_code(code, node, child)
                if found:
                    return found, parent_code

        return None, None

    code = request.GET.get("code", None)
    if code:
        found_code_data, parent_code = find_code(code, {"code": None}, tree_data)
        print(found_code_data)
        print(parent_code)
        if found_code_data:
            tree_data = found_code_data

    return render(
        request,
        "cut_of_funds_table.html",
        {
            "year": year,
            "bar_colors": "2" if tree_type == "expenses" else "1",
            "tree_data": tree_data,
            "tree_type": tree_type,
            "parent_code": parent_code,
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
