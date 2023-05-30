from django.shortcuts import render
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.http import JsonResponse

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
    MunicipalityFinancialYear,
)
from obcine.tree_utils import ExpenseTreeBuilder, RevenueTreeBuilder


def get_year(year_id):
    if year_id:
        return FinancialYear.objects.get(id=year_id)
    else:
        return FinancialYear.objects.last()

def get_tree_type(query_dict):
    return "expenses" if query_dict.get("type", "") == "expenses" else "revenue"

def get_cache_key(municipality, year, endpoint, type):
    mfy = MunicipalityFinancialYear.objects.filter(
        financial_year=year,
        municipality=municipality
    ).first()
    cache_key = f'{endpoint}_{type}_{municipality.id}_{year.id}_{mfy.updated_at.isoformat()}'
    return cache_key

def get_summary(municipality, year, summary_type="monthly"):
    summary_cache_key = get_cache_key(municipality, year, 'summary', summary_type)

    data = cache.get(summary_cache_key)
    if data:
        return data

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

    cache.set(summary_cache_key, summary)

    return summary

def get_revenue_tree(municipality, year, summary, summary_type="monthly"):
    revenue_tree_cache_key = get_cache_key(municipality, year, 'revenue_tree', summary_type)

    data = cache.get(revenue_tree_cache_key)
    if data:
        return data

    rtb = RevenueTreeBuilder(
        RevenueDefinition,
        municipality=municipality,
        financial_year=year,
    )

    if summary_type == "monthly":
        merged_tree_revenues = rtb.get_merged_revenue_tree(
            PlannedRevenue,
            MonthlyRevenue,
        )

        data = {
            "planned": summary["planned_revenue"],
            "realized": summary["realized_revenue"],
            "name": "Celotni prihodki",
            "code": None,
            "children": merged_tree_revenues,
        }

    elif summary_type == "yearly":
        realized_revenue = rtb.get_revenue_tree(YearlyRevenue)

        data = {
            "realized": summary["realized_revenue"],
            "name": "Celotni prihodki",
            "code": None,
            "children": realized_revenue,
        }
    else:
        raise TypeError

    cache.set(revenue_tree_cache_key, data)
    return data

def get_expense_tree(municipality, year, summary, summary_type="monthly"):
    expense_tree_cache_key = get_cache_key(municipality, year, 'expense_tree', summary_type)
    data = cache.get(expense_tree_cache_key)
    if data:
        return data

    etb = ExpenseTreeBuilder(
        municipality=municipality,
        financial_year=year,
    )

    if summary_type == "monthly":
        merged_tree_expenses = etb.get_merged_expense_tree(
            PlannedExpense,
            MonthlyExpense,
        )

        data = {
            "planned": summary["planned_expenses"],
            "realized": summary["realized_expenses"],
            "name": "Celotni odhodki",
            "code": None,
            "children": merged_tree_expenses,
        }

    elif summary_type == "yearly":
        realized_expenses = etb.get_expense_tree(YearlyExpense)

        data = {
            "realized": summary["realized_expenses"],
            "name": "Celotni odhodki",
            "code": None,
            "children": realized_expenses,
        }
    else:
        raise TypeError

    cache.set(expense_tree_cache_key, data)
    return data

def overview(request, municipality_id, year_id=None):
    municipality = Municipality.objects.get(id=municipality_id)
    year = get_year(year_id)

    summary_type = "monthly" if year.is_current() else "yearly"
    summary = get_summary(municipality, year, summary_type=summary_type)

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

    revenue = get_revenue_tree(municipality, year, summary, summary_type)
    expenses = get_expense_tree(municipality, year, summary, summary_type)

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

def comparison_over_time(request, municipality_id, year_id=None):
    municipality = Municipality.objects.get(id=municipality_id)
    year = get_year(year_id)
    tree_type = get_tree_type(request.GET)

    return render(
        request,
        "comparison_over_time.html",
        {
            "municipality": municipality,
            "year": year,
            "tree_type": tree_type,
            "years": FinancialYear.objects.all(),  # TODO: only show valid years for this municipality
        },
    )

def get_context_for_table_code(request, municipality_id, year_id=None):
    municipality = Municipality.objects.get(id=municipality_id)
    year = get_year(year_id)
    tree_type = get_tree_type(request.GET)

    summary_type = "monthly" if year.is_current() else "yearly"
    summary = get_summary(municipality, year, summary_type=summary_type)

    tree_data = []
    tree_parents = []

    if tree_type == "expenses":
        tree_data = get_expense_tree(municipality, year, summary, summary_type)
    else:
        tree_data = get_revenue_tree(municipality, year, summary, summary_type)

    def find_code(code, parent_chain, node):
        if node["code"] == code:
            return node, parent_chain

        if children := node.get("children", []):
            for child in children:
                found, found_parent_chain = find_code(
                    code, [*parent_chain, node], child
                )
                if found:
                    return found, found_parent_chain

        return None, None

    code = request.GET.get("code", None)
    if code:
        found_code_data, found_parent_chain = find_code(
            code, [{"code": None}], tree_data
        )
        if found_code_data:
            tree_parents = found_parent_chain[1:]
            tree_data = found_code_data

    return {
        "summary": summary,
        "year": year,
        "bar_colors": "2" if tree_type == "expenses" else "1",
        "tree_data": tree_data,
        "tree_type": tree_type,
        "tree_parents": tree_parents,
    }

def cut_of_funds_table(request, municipality_id, year_id=None):
    return render(
        request,
        "cut_of_funds_table.html",
        get_context_for_table_code(request, municipality_id, year_id),
    )

def comparison_over_time_table(request, municipality_id, year_id=None):
    return render(
        request,
        "comparison_over_time_table.html",
        get_context_for_table_code(request, municipality_id, year_id),
    )

def comparison_over_time_chart_data(request, municipality_id, year_id=None):
    municipality = Municipality.objects.get(id=municipality_id)
    year = get_year(year_id)
    tree_type = get_tree_type(request.GET)

    years_data = {}
    years = FinancialYear.objects.all()  # TODO: only show valid years for this municipality
    # years = municipality.financial_years.filter(municipalityfinancialyears__is_published=True)

    for year_ in years:
        summary_type = "monthly" if year_.is_current() else "yearly"
        summary = get_summary(municipality, year_, summary_type=summary_type)

        if tree_type == "expenses":
            tree_data = get_expense_tree(municipality, year_, summary, summary_type)
        else:
            tree_data = get_revenue_tree(municipality, year_, summary, summary_type)

        years_data[year_.name] = tree_data["children"]

    return JsonResponse({
        "year": year.name,
        "years_data": years_data,
        "tree_type": tree_type,
    })
