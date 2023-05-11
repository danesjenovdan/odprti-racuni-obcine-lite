from django.shortcuts import render
from django.views.decorators.cache import cache_page

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


def get_revenue_tree(municipality, year, summary, summary_type="monthly"):
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

        return {
            "planned": summary["planned_revenue"],
            "realized": summary["realized_revenue"],
            "name": "Celotni prihodki",
            "code": None,
            "children": merged_tree_revenues,
        }

    elif summary_type == "yearly":
        realized_revenue = rtb.get_revenue_tree(YearlyRevenue)

        return {
            "realized": summary["realized_revenue"],
            "name": "Celotni prihodki",
            "code": None,
            "children": realized_revenue,
        }


def get_expense_tree(municipality, year, summary, summary_type="monthly"):
    etb = ExpenseTreeBuilder(
        municipality=municipality,
        financial_year=year,
    )

    if summary_type == "monthly":
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

    elif summary_type == "yearly":
        realized_expenses = etb.get_expense_tree(YearlyExpense)

        return {
            "realized": summary["realized_expenses"],
            "name": "Celotni odhodki",
            "code": None,
            "children": realized_expenses,
        }

@cache_page(60 * 60 * 24)
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

@cache_page(60 * 60 * 24)
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

@cache_page(60 * 60 * 24)
def cut_of_funds_table(request, municipality_id, year_id=None):
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

    return render(
        request,
        "cut_of_funds_table.html",
        {
            "summary": summary,
            "year": year,
            "bar_colors": "2" if tree_type == "expenses" else "1",
            "tree_data": tree_data,
            "tree_type": tree_type,
            "tree_parents": tree_parents,
        },
    )

@cache_page(60 * 60 * 24)
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
        },
    )

@cache_page(60 * 60 * 24)
def comparison_over_time_table(request, municipality_id, year_id=None):
    municipality = Municipality.objects.get(id=municipality_id)
    year = get_year(year_id)
    tree_type = get_tree_type(request.GET)

    current_tree_data = []
    current_tree_parents = []
    years_data = {}
    years = municipality.financial_years.filter(municipalityfinancialyears__is_published=True)
    for year_ in years:
        summary_type = "monthly"  if year_.is_current() else "yearly"
        summary = get_summary(municipality, year_, summary_type)

        tree_data = []
        tree_parents = []

        if tree_type == "expenses":
            tree_data = get_expense_tree(municipality, year_, summary, summary_type)
        else:
            tree_data = get_revenue_tree(municipality, year_, summary, summary_type)

        # #TODO Tole probi deprecatat

        # def find_code(code, parent_chain, node):
        #     if node["code"] == code:
        #         return node, parent_chain

        #     if children := node.get("children", []):
        #         for child in children:
        #             found, found_parent_chain = find_code(
        #                 code, [*parent_chain, node], child
        #             )
        #             if found:
        #                 return found, found_parent_chain

        #     return None, None

        # code = request.GET.get("code", None)
        # if code:
        #     found_code_data, found_parent_chain = find_code(
        #         code, [{"code": None}], tree_data
        #     )
        #     if found_code_data:
        #         tree_parents = found_parent_chain[1:]
        #         tree_data = found_code_data

        #print(tree_data)

        years_data[year_.name] = tree_data["children"]
        if year_ == year:
            current_tree_data = tree_data
            current_tree_parents = tree_parents

    return render(
        request,
        "comparison_over_time_table.html",
        {
            "years": years,
            "summary": summary,
            "year": year,
            "bar_colors": "2" if tree_type == "expenses" else "1",
            "tree_data": current_tree_data,
            "tree_type": tree_type,
            "tree_parents": current_tree_parents,
            # ---
            "years_data": years_data,
        },
    )
