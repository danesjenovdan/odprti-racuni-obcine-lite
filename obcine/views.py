from datetime import datetime

from django.core.cache import cache
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import cache_page
from django.views.generic import RedirectView

from obcine.models import (
    FinancialYear,
    MonthlyExpense,
    MonthlyRevenue,
    Municipality,
    MunicipalityFinancialYear,
    PlannedExpense,
    PlannedRevenue,
    RevenueDefinition,
    YearlyExpense,
    YearlyRevenue,
)
from obcine.tree_utils import ExpenseTreeBuilder, RevenueTreeBuilder


class OldUrlRedirectView(RedirectView):
    permanent = False
    query_string = True

    def get_redirect_url(self, *args, **kwargs):
        new_kwargs = {}

        if municipality_id := kwargs.get("municipality_id"):
            municipality = get_object_or_404(Municipality, pk=municipality_id)
            new_kwargs["municipality_slug"] = municipality.slug

        if year_id := kwargs.get("year_id"):
            year = get_object_or_404(FinancialYear, pk=year_id)
            new_kwargs["year_slug"] = slugify(year.name)

        return super().get_redirect_url(*args, **new_kwargs)


def landing(request):
    return render(request, "landing.html")

def get_summary_type(municipality, year):
    summary_type = "monthly" if year.is_current() else "yearly"
    # WORKAROUND: if there are no yearly expenses, show monthly expenses
    yearly_expense = YearlyExpense.objects.filter(municipality=municipality, year=year)
    if not yearly_expense:
        summary_type = "monthly"
    return summary_type

def get_year(year_slug, municipality):
    year_id = get_object_or_404(FinancialYear, name=year_slug).id if year_slug else None

    municipality_financial_year = MunicipalityFinancialYear.objects.filter(
        financial_year_id=year_id,
        municipality=municipality,
        is_published=True,
    )
    if municipality_financial_year:
        return municipality_financial_year.first().financial_year

    municipality_financial_year = MunicipalityFinancialYear.objects.filter(
        financial_year__name=str(datetime.now().year),
        municipality=municipality,
        is_published=True,
    )

    if municipality_financial_year:
        return municipality_financial_year.first().financial_year

    municipality_financial_year = (
        MunicipalityFinancialYear.objects.filter(
            municipality=municipality,
            is_published=True,
        )
        .order_by("-financial_year__name")
        .first()
    )
    if municipality_financial_year:
        return municipality_financial_year.financial_year
    else:
        raise Http404(_("No published financial year found"))


def get_municipality_published_years(municipality):
    municipality_financial_year = [
        i.financial_year
        for i in MunicipalityFinancialYear.objects.filter(
            municipality=municipality,
            is_published=True,
        ).order_by("financial_year__name")
    ]
    return municipality_financial_year


def get_tree_type(query_dict):
    return "expenses" if query_dict.get("type", "") == "expenses" else "revenue"


def get_cache_key(municipality, year, endpoint, type):
    mfy = MunicipalityFinancialYear.objects.filter(
        financial_year=year, municipality=municipality
    ).first()
    cache_key = (
        f"{endpoint}_{type}_{municipality.id}_{year.id}_{mfy.updated_at.isoformat()}"
    )
    return cache_key


def get_document_date(data_model, municipality, year):
    obj = (
        data_model.objects.filter(municipality=municipality, year=year)
        .filter(document__timestamp__isnull=False)
        .order_by("-document__timestamp")
        .first()
    )
    if obj:
        return obj.document.timestamp
    return None


def get_summary(municipality, year, summary_type="monthly"):
    summary_cache_key = get_cache_key(municipality, year, "summary2", summary_type)

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
            "realized_expenses_date": get_document_date(MonthlyExpense, municipality, year),
            "realized_revenue_date": get_document_date(MonthlyRevenue, municipality, year),
        }

    elif summary_type == "yearly":
        realized_expenses = etb.get_expense_tree(YearlyExpense)
        realized_revenue = rtb.get_revenue_tree(YearlyRevenue)

        summary = {
            "realized_expenses": sum([i["amount"] for i in realized_expenses]),
            "realized_revenue": sum([i["amount"] for i in realized_revenue]),
            "realized_expenses_date": get_document_date(YearlyExpense, municipality, year),
            "realized_revenue_date": get_document_date(YearlyRevenue, municipality, year),
        }

    summary_keys = list(filter(lambda k: not k.endswith("_date"), summary.keys()))
    summary_max_value = max([summary[k] for k in summary_keys])
    for key in summary_keys:
        summary[f"{key}_percentage"] = (
            summary[key] / summary_max_value if summary_max_value > 0 else 0
        )

    summary["summary_type"] = summary_type

    cache.set(summary_cache_key, summary)

    return summary


def get_revenue_tree(municipality, year, summary, summary_type="monthly"):
    revenue_tree_cache_key = get_cache_key(
        municipality, year, "revenue_tree", summary_type
    )

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
    expense_tree_cache_key = get_cache_key(
        municipality, year, "expense_tree", summary_type
    )
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

def overview(request, municipality_slug, year_slug=None):
    municipality = get_object_or_404(Municipality, slug=municipality_slug)
    year = get_year(year_slug, municipality)
    mfy = year.municipalityfinancialyears.filter(municipality=municipality).first()

    summary_type = get_summary_type(municipality, year)
    summary = get_summary(municipality, year, summary_type=summary_type)

    return render(
        request,
        "overview.html",
        {
            "municipality": municipality,
            "municipality_financial_year": mfy,
            "year": year,
            "summary": summary,
        },
    )


def cut_of_funds(request, municipality_slug, year_slug=None):
    municipality = get_object_or_404(Municipality, slug=municipality_slug)
    year = get_year(year_slug, municipality)
    mfy = year.municipalityfinancialyears.filter(municipality=municipality).first()
    tree_type = get_tree_type(request.GET)

    summary_type = get_summary_type(municipality, year)

    summary = get_summary(municipality, year, summary_type=summary_type)

    revenue = get_revenue_tree(municipality, year, summary, summary_type)
    expenses = get_expense_tree(municipality, year, summary, summary_type)

    return render(
        request,
        "cut_of_funds.html",
        {
            "years": get_municipality_published_years(municipality),
            "municipality": municipality,
            "municipality_financial_year": mfy,
            "year": year,
            "summary": summary,
            "revenue": revenue,
            "expenses": expenses,
            "tree_type": tree_type,
        },
    )


def get_context_for_table_code(request, municipality_slug, year_slug=None):
    municipality = get_object_or_404(Municipality, slug=municipality_slug)
    year = get_year(year_slug, municipality)
    mfy = year.municipalityfinancialyears.filter(municipality=municipality).first()
    tree_type = get_tree_type(request.GET)

    summary_type = get_summary_type(municipality, year)
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
        else:
            tree_data = {
                "realized": 0,
                "name": "Not found",
                "code": None,
                "children": [],
            }
            tree_parents = []

    return {
        "summary": summary,
        "year": year,
        "municipality_financial_year": mfy,
        "bar_colors": "2" if tree_type == "expenses" else "1",
        "tree_data": tree_data,
        "tree_type": tree_type,
        "tree_parents": tree_parents,
    }


def cut_of_funds_table(request, municipality_slug, year_slug=None):
    return render(
        request,
        "cut_of_funds_table.html",
        get_context_for_table_code(request, municipality_slug, year_slug),
    )
