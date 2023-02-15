from django.db.models import Sum


class RevenueTreeBuilder():
    def __init__(self, definition_model, municipality, financial_year, leave_parent_key='definition'):
        self.municipality = municipality
        self.financial_year = financial_year
        self.definiton_storage = definition_model.get_id_value_dict()
        self.leave_parent_key = leave_parent_key

    def get_revenue_tree(self, data_model):
        revenues = data_model.objects.filter(municipality=self.municipality, year=self.financial_year)
        revenues = revenues.values('code', self.leave_parent_key, 'amount').annotate(sum_amount=Sum('amount'))

        leaves = []
        definiton_keys = self.definiton_storage.keys()
        for revenue in revenues:
            if not revenue[self.leave_parent_key] in definiton_keys:
                # skip unvalid items
                continue
            item = self.definiton_storage[revenue[self.leave_parent_key]]
            item.amount = revenue['sum_amount']
            item.children = []
            leaves.append(item.get_offline_dict())

        return self.build_tree(leaves)

    def build_tree(self, items):
        parent_level = {}
        parent = None
        print('Build level')
        for item in items:
            parent = self.definiton_storage[item['parent_id']]
            if parent.id in parent_level.keys():
                parent_level[parent.id]['amount'] += item['amount']
                parent_level[parent.id]['children'].append(item)
            else:
                parent.amount = item['amount']
                parent.children = [item]
                parent_level[parent.id] = parent.get_offline_dict()

        if parent and parent.parent:
            return self.build_tree(parent_level.values())
        else:
            return parent_level


class ExpanseTreeBuilder():
    def __init__(self, municipality, financial_year):
        self.municipality = municipality
        self.financial_year = financial_year

    def get_expense_tree(self, data_model):
        expenses = data_model.objects.filter(municipality=self.municipality, year=self.financial_year)
        self.definiton_storage = {expense.id: expense for expense in expenses}
        expenses = expenses.filter(
            level=4
        ).values(
            'code',
            'parent',
            'amount'
        ).annotate(
            sum_amount=Sum('amount')
        )
        leaves = []
        for expense in expenses:
            item = self.definiton_storage[expense['parent']]
            item.amount = expense['amount']
            item.children = []
            leaves.append(item.get_offline_dict())
        return list(self.build_tree(leaves).values())

    def build_tree(self, items):
        parent_level = {}
        parent = None
        print('Build level')
        for item in items:
            parent = self.definiton_storage[item['parent_id']]
            if parent.id in parent_level.keys():
                parent_level[parent.id]['amount'] += item['amount']
                parent_level[parent.id]['children'].append(item)
            else:
                parent.amount = item['amount']
                parent.children = [item]
                parent_level[parent.id] = parent.get_offline_dict()

        if parent and parent.parent:
            return self.build_tree(parent_level.values())
        else:
            return parent_level
