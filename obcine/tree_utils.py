from django.db.models import Sum
from mptt.utils import get_cached_trees


def build_tree(definiton_storage, items):
    parent_level = {}
    parent = None

    for item in items:
        parent = definiton_storage[item["parent_id"]]
        if parent.id in parent_level.keys():
            parent_level[parent.id]["amount"] += item["amount"]
            parent_level[parent.id]["children"].append(item)
        else:
            parent.amount = item["amount"]
            parent.children = [item]
            parent_level[parent.id] = parent.get_offline_dict()

    if parent and parent.parent:
        return build_tree(definiton_storage, parent_level.values())
    else:
        return parent_level


def build_merged_tree(definiton_storage, items):
    parent_level = {}
    parent = None

    for item in items:
        parent = definiton_storage[item["parent_id"]]
        if parent.id in parent_level.keys():
            parent_level[parent.id]["planned"] += item["planned"]
            parent_level[parent.id]["realized"] += item["realized"]
            parent_level[parent.id]["children"].append(item)
        else:
            parent.amount = item["planned"]
            parent.children = [item]
            parent_level[parent.id] = parent.get_offline_dict()
            parent_level[parent.id].pop("amount")
            parent_level[parent.id]["planned"] = item["planned"]
            parent_level[parent.id]["realized"] = item["realized"]

    if parent and parent.parent:
        return build_merged_tree(definiton_storage, parent_level.values())
    else:
        return parent_level


def get_nested_dictionary_from_tree(queryset, remove_amount):
        roots = get_cached_trees(queryset)

        def form_a_tree(objects):
            tree = dict()

            for obj in objects:
                children = obj.get_children()
                dictionary_category_tree = obj.get_offline_dict_keyed_children()
                if remove_amount:
                    dictionary_category_tree['realized'] = 0
                    dictionary_category_tree['planned'] = dictionary_category_tree['amount']
                    dictionary_category_tree.pop('amount')

                if children:
                    dictionary_category_tree.update({'children': form_a_tree(children)})

                tree[dictionary_category_tree['code']] = dictionary_category_tree

            return tree

        return form_a_tree(roots)

class RevenueTreeBuilder:
    def __init__(
        self,
        definition_model,
        municipality,
        financial_year,
        leaf_parent_key="definition",
    ):
        self.municipality = municipality
        self.financial_year = financial_year
        self.definiton_storage = definition_model.get_id_value_dict()
        self.leaf_parent_key = leaf_parent_key

    def get_revenue_tree(self, data_model):
        revenues = data_model.objects.filter(
            municipality=self.municipality,
            year=self.financial_year,
        )
        revenues = revenues.values(
            "code",
            self.leaf_parent_key,
            "amount",
        ).annotate(
            sum_amount=Sum("amount"),
        )

        leaves = []
        definiton_keys = self.definiton_storage.keys()
        for revenue in revenues:
            if not revenue[self.leaf_parent_key] in definiton_keys:
                continue  # skip invalid items
            item = self.definiton_storage[revenue[self.leaf_parent_key]]
            item.amount = revenue["sum_amount"]
            item.children = []
            leaves.append(item.get_offline_dict())

        return list(build_tree(self.definiton_storage, leaves).values())

    def get_merged_revenue_tree(self, planned_data_model, realized_data_model):
        planned_revenues = planned_data_model.objects.filter(
            municipality=self.municipality,
            year=self.financial_year,
        )
        planned_revenues = planned_revenues.values(
            "code",
            self.leaf_parent_key,
            "amount",
        ).annotate(
            sum_amount=Sum("amount"),
        )

        realized_revenues = realized_data_model.objects.filter(
            municipality=self.municipality,
            year=self.financial_year,
        )
        realized_revenues = realized_revenues.values(
            "code",
            self.leaf_parent_key,
            "amount",
        ).annotate(
            sum_amount=Sum("amount"),
        )
        realized_dict = {item["code"]: item["amount"] for item in realized_revenues}

        leaves = []
        definiton_keys = self.definiton_storage.keys()
        for revenue in planned_revenues:
            if not revenue[self.leaf_parent_key] in definiton_keys:
                continue  # skip invalid items
            item = self.definiton_storage[revenue[self.leaf_parent_key]]
            item.amount = revenue["sum_amount"]
            item.children = []
            item_dict = item.get_offline_dict()
            item_dict["planned"] = item_dict.pop("amount")
            item_dict["realized"] = realized_dict.get(item_dict["code"], 0)
            leaves.append(item_dict)

        return list(build_merged_tree(self.definiton_storage, leaves).values())


class ExpenseTreeBuilder:
    def __init__(self, municipality, financial_year):
        self.municipality = municipality
        self.financial_year = financial_year

    def get_expense_tree(self, data_model):
        expenses = data_model.objects.filter(
            municipality=self.municipality,
            year=self.financial_year,
        )
        self.definiton_storage = {expense.id: expense for expense in expenses}
        return list(build_tree(self.definiton_storage, [expanse.get_offline_dict() for expanse in expenses.filter(level=4)]).values())

    def get_merged_expense_tree(self, planned_data_model, realized_data_model):
        planned_expenses = planned_data_model.objects.filter(
            municipality=self.municipality,
            year=self.financial_year,
        )
        realized_expenses = realized_data_model.objects.filter(
            municipality=self.municipality,
            year=self.financial_year,
        )
        planned_tree = get_nested_dictionary_from_tree(planned_expenses, remove_amount=True)
        realized_tree = get_nested_dictionary_from_tree(realized_expenses, remove_amount=False)


        def update_realized(subtree, realized_subtree):
            for item in subtree.values():
                if item['code'] in realized_subtree.keys():
                    item['realized'] = realized_subtree[item['code']]['amount']
                    if 'children' in item.keys():
                        update_realized(item['children'], realized_subtree[item['code']]['children'])


        def listify_children(tree):
            print('listify')
            tree = list(tree.values())
            for item in tree:
                if 'children' in item.keys():
                    item['children'] = listify_children(item['children'])
            return list(tree)

        update_realized(planned_tree, realized_tree)

        planned_tree = listify_children(planned_tree)
        return planned_tree
