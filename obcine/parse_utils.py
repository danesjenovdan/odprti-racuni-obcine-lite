import xlrd
import time
import requests
from django.db import transaction


class XLSXAppraBudget(object):
    def __init__(self, document, model, definiton_model=None):
        self.municipality = document.municipality_year.municipality
        self.year = document.municipality_year.financial_year
        self.model = model
        self.document_object = document
        self.municipality_year = document.municipality_year

    def prepare_moodel(self, name, code, order):
        obj = self.model(
                    name=name,
                    code=code,
                    order=order,
                    municipality=self.municipality,
                    year=self.year,
                    document=self.document_object,
                    #municipality_year=self.municipality_year
                )
        return obj

    def parse_file(self, file_path='files/proracun_apra.xlsx'):
        book = xlrd.open_workbook(file_path)
        sheet = book.sheet_by_index(0)

        # delete previous data
        self.model.objects.filter(
            year=self.year,
            municipality=self.municipality
        ).delete()

        nodes = {}
        node_keys = []
        i=0
        print(range(sheet.nrows))
        start_time = time.time()
        for row_i in range(sheet.nrows):
            # skip first row
            if i == 0:
                i+=1
                continue

            # get first level data and save it
            row = sheet.row(row_i)
            ppp_id = row[2].value.strip()
            ppp_name = row[3].value.strip()

            if ppp_id in node_keys:
                ppp = nodes[ppp_id]
            else:
                ppp = self.prepare_moodel(
                    name=ppp_name,
                    code=ppp_id,
                    order=i,
                )
                ppp.save()
                i+=1
                nodes[ppp_id] = ppp
                node_keys.append(ppp_id)

            # get second level data and save it
            gpr_id = row[4].value.strip()
            gpr_name = row[5].value.strip()

            if gpr_id in node_keys:
                gpr = nodes[gpr_id]
            else:
                gpr = self.prepare_moodel(
                    name=gpr_name,
                    code=gpr_id,
                    order=i,
                )
                gpr.parent=ppp
                gpr.save()
                i+=1
                nodes[gpr_id] = gpr
                node_keys.append(gpr_id)

            # get third level data and save it, or update amount on existed
            ppr_id = row[6].value.strip()
            ppr_name = row[7].value.strip()

            amount = row[16].value

            if ppr_id in node_keys:
                ppr = nodes[ppr_id]
                #ppr.amount += amount
                #ppr.save()
            else:
                ppr = self.prepare_moodel(
                    name=ppr_name,
                    code=ppr_id,
                    order=i,
                )
                ppr.parent=gpr
                #ppr.amount=amount
                ppr.save()
                i+=1
                nodes[ppr_id] = ppr
                node_keys.append(ppr_id)

            # Do tuki je ok

            pp_id = f'fk{row[8].value.strip()}'
            pp_name = row[9].value.strip()
            ppr_pp_id = f'{ppr_id}_{pp_id}'

            if ppr_pp_id in node_keys:
                pp = nodes[ppr_pp_id]
            else:
                pp = self.prepare_moodel(
                    name=pp_name,
                    code=pp_id,
                    order=i,
                )
                pp.parent=ppr
                pp.save()
                i+=1
                nodes[ppr_pp_id] = pp
                node_keys.append(ppr_pp_id)

            k4_id = row[10].value.strip()
            k4_name = row[11].value.strip()
            amount = row[16].value
            ppr_pp_k4_id = f'{ppr_pp_id}_{k4_id}'

            if ppr_pp_k4_id in node_keys:
                k4 = nodes[ppr_pp_k4_id]
            else:
                k4 = self.prepare_moodel(
                    name=k4_name,
                    code=k4_id,
                    order=i,
                )

                k4.parent=pp
                k4.amount=amount
                k4.save()
                i+=1
                nodes[k4_id] = k4
                node_keys.append(k4_id)

        for budget_item in self.model.objects.filter(document=self.document_object, level=3, amount=None):
            budget_item.amount = sum([item.amount for item in budget_item.get_children()])
            budget_item.save()

        for budget_item in self.model.objects.filter(document=self.document_object, level=2, amount=None):
            budget_item.amount = sum([item.amount for item in budget_item.get_children()])
            budget_item.save()

        for budget_item in self.model.objects.filter(document=self.document_object, level=1, amount=None):
            budget_item.amount = sum([item.amount for item in budget_item.get_children()])
            budget_item.save()

        for budget_item in self.model.objects.filter(document=self.document_object, level=0, amount=None):
            budget_item.amount = sum([item.amount for item in budget_item.get_children()])
            budget_item.save()

        self.municipality_year.save()
        print("--- %s seconds ---" % (time.time() - start_time))


class XLSXAppraRevenue(object):
    def __init__(self, document, model, definiton_model):
        self.municipality = document.municipality_year.municipality
        self.year = document.municipality_year.financial_year
        self.municipality_year = document.municipality_year
        self.model = model
        self.document_object = document
        self.definiton_model = definiton_model
        definitons_qeryset = definiton_model.objects.all()
        self.definitons = {d.code: d for d in definitons_qeryset}


    def prepare_moodel(self, name, code, amount):
        konto_6 = code[:6]
        obj = self.model(
                    name=name,
                    code=konto_6,
                    municipality=self.municipality,
                    year=self.year,
                    document=self.document_object,
                    definition=self.definitons.get(konto_6, None),
                    amount=amount,
                )
        return obj

    def parse_file(self, file_path='files/proracun_apra.xlsx'):

        # delete previous data
        self.model.objects.filter(
            year=self.year,
            municipality=self.municipality
        ).delete()

        book = xlrd.open_workbook(file_path)
        sheet = book.sheet_by_index(0)

        nodes = {}
        i=0
        for row_i in range(sheet.nrows):
            # skip first row
            if i == 0:
                i+=1
                continue

            # get first level data and save it
            row = sheet.row(row_i)
            k6_id = row[1].value.strip()
            k6_name = row[2].value.strip()
            k6_amount = row[3].value

            print(k6_id, k6_name, k6_amount)

            k6 = self.prepare_moodel(
                name=k6_name,
                code=k6_id,
                amount=k6_amount
            )
            k6.save()

        self.municipality_year.save()

# class XLSParser(object):
#     def __init__(self):
#         self.depths = {}
#         self.org = Municipality.objects.get(id=1)
#         self.year = FinancialYear.objects.first()
#         self.parse_file()

#     def parse_line(self, line):
#         return [(i, item) for i, item in enumerate(line) if item]

#     def get_parent_node(self, depth, last_added):
#         current = last_added
#         while self.depths[current.id] >= depth:
#             current = current.parent
#             if not current:
#                 return None
#         return current


#     def parse_file(self, file_path='files/prihodki_ajdovscina_2022.xls'):
#         book = xlrd.open_workbook(file_path)
#         sheet = book.sheet_by_index(0)

#         rows = []
#         for row_i in range(sheet.nrows):
#             row_values = []
#             for cell in sheet.row(row_i):
#                 row_values.append(cell.value)
#             rows.append(row_values)

#         parent = None

#         last_added = None

#         i = 0
#         for row in rows:
#             items = self.parse_line(row)
#             if len(items) != 3:
#                 continue
#             print(items)
#             if last_added:
#                 parent = self.get_parent_node(items[0][0], last_added)
#             else:
#                 parent = None

#             rc = RevenueObcine(
#                 name=items[1][1],
#                 amount=items[2][1],
#                 code=items[0][1],
#                 parent=parent,
#                 order=i,
#                 organization=self.org,
#                 year=self.year)
#             rc.save()
#             self.depths[rc.id] = int(items[0][0])
#             last_added = rc
#             i+=1



class XLSCodesParser(object):
    def __init__(self, model):
        self.depths = {}
        self.model = model
        self.parse_file()


    def parse_line(self, line):
        return [(i, item) for i, item in enumerate(line) if item]

    def get_parent_node(self, depth, last_added):
        current = last_added
        while self.depths[current.id] >= depth:
            current = current.parent
            if not current:
                return None
        return current


    def parse_file(self, file_path='files/kode_matic.xlsx'):
        book = xlrd.open_workbook(file_path)
        sheet = book.sheet_by_index(2)

        rows = []
        for row_i in range(sheet.nrows):
            row_values = []
            for cell in sheet.row(row_i):
                row_values.append(cell.value)
            rows.append(row_values)

        parent = None

        last_added = None

        i = 0
        for row in rows:
            items = self.parse_line(row)
            if len(items) != 2:
                continue
            print(items)
            if last_added:
                parent = self.get_parent_node(items[0][0], last_added)
            else:
                parent = None
            print('pre save')
            rc = self.model(
                name=items[1][1],
                code=int(items[0][1]),
                parent=parent,
                order=i)
            rc.save()
            self.depths[rc.id] = int(items[0][0])
            last_added = rc
            i+=1


def download_file(url, name):
    response = requests.get(url)
    file_path = f'media/{name}'
    with open(file_path, 'wb') as f:
        f.write(response.content)
    return file_path
