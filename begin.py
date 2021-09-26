# Module Imports
import mariadb
import sys
from openpyxl.workbook import child
from pprintpp import pprint as pp # optional
from readKP import get_data_excel

COMPANY_NAME = "GRADIENT"

#  mysql -u makometr -p -h localhost
def openBDConnection():
    try:    
        conn = mariadb.connect(
            user="user",
            password="1202",
            host="localhost",
            port=3306,
            database="_ea34ba56edc5b4ee"
        )
    except mariadb.Error as e:
        print(f"Ошибка подключения к Базе Данных: {e}")
        sys.exit(1)
    return conn

def findColumns(naming):
    name_index, amount_index, price_index = None, None, None
    for i, col_name in enumerate(naming):
        col_name = col_name.lower()
        if "наименование" in col_name:
            if name_index is not None:
                print("Внимание! Найдено несколько столбцов с названием. Будет обработан последний.")
            name_index = i
        if "к-во" in col_name or "количество" in col_name:
            if amount_index is not None:
                print("Внимание! Найдено несколько столбцов с количеством. Будет обработан последний.")
            amount_index = i
        if "цена" in col_name:
            if price_index is not None:
                print("Внимание! Найдено несколько столбцов с ценой. Будет обработан последний.")
            price_index = i
    return name_index, amount_index, price_index


def insertTasksInProjects(cur, excel_data, projname):
    TMP_ID = 1
    # проект-TASK-ID

    queryParent = f"INSERT INTO tabTask(name, subject, project, creation, owner, status, is_group, price, amount, depends_on_tasks) " \
            "VALUES(%s,%s,%s,%s,%s,%s,'1','0',%s, %s)"
    queryChild  = f"INSERT INTO tabTask(name, subject, project, creation, owner, status, parent_task, price, amount, progress_amount) " \
            "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s, 0)"
    query = f"INSERT INTO `tabCustomer Dict Catalog`(name, creation, owner, \
            term_customer, section, work_type, materials_group, term_worker, contragent_id, price_customer, price_worker, price_contragent) " \
            "VALUES(%s,%s,%s, %s,%s,%s,%s,%s,%s,%s,%s,%s)"
    for task in excel_data:
        parent_name = task["name"]
        name_col, amount_col, price_col = findColumns(task["naming"])
        parent_ID = projname + "-TASK-" + str(TMP_ID)
        parent_data = [parent_ID, parent_name, projname, "2021-05-25 08:02:14.204645", "Administrator", "Working", str(len(task["inner_tasks"]))]
        children = ""
        data1 = [parent_ID, "2021-05-25 08:02:14.204645", "Administrator", parent_name, parent_name, "", "", "", 0, 0, 0, 0]
        cur.execute(query, data1)
        TMP_ID += 1
        for inner_task in task["inner_tasks"]:
            ID = projname + "-TASK-" + str(TMP_ID)
            name_custoner = inner_task[name_col]
            if price_col is None:
                price_customer = 0.0
            else:
                price_customer = inner_task[price_col]
            data1 = [ID, "2021-05-25 08:02:14.204645", "Administrator",
                    name_custoner, parent_name, "", "", "", 0, price_customer, 0, 0]
            cur.execute(query, data1)
            children += str(ID) + ","
            if amount_col is None:
                amount = 0
            elif inner_task[amount_col] is None:
                amount = 0
            else:
                amount = inner_task[amount_col]
            if inner_task[price_col] != None:
                price = inner_task[price_col]
            else:
                price = 0
            data = [ID, inner_task[name_col], projname, "2021-05-25 08:02:14.204645", "Administrator", "Working", parent_ID, price, amount]
            cur.execute(queryChild, data)
            conn.commit()
            TMP_ID += 1
            print(cur.rowcount, "Record inserted successfully into Laptop table")


        parent_data.append(children)
        # print(parent_data)
        cur.execute(queryParent, parent_data)
        conn.commit()
        print(cur.rowcount, "Record inserted successfully into Laptop table")

def checkProjectExists(cur, proj_name):
    cur.execute(f"select count(1) from tabProject where name = %s", [proj_name])
    answer = cur.fetchone()[0]
    if answer == 1:
        return True
    else:
        return False


def insertProject(cur, projname):
    if checkProjectExists(cur, projname):
        print("Внимание: проект с таким названием уже существует.")
        return
    print("Внимание: проекта с таким названием не существует. Будет создан новый.")

    query = f"INSERT INTO tabProject(name, creation, owner, project_name, status, is_active, company) " \
        "VALUES(%s,%s,%s,%s,%s,%s,%s)"
    data = [projname, "2021-05-25 08:02:14.204645", "Administrator", projname, "Open", "Yes", COMPANY_NAME]

    cur.execute(query, data)
    conn.commit()





def insertDictCatalog(cur, excel_data, proj_name):
    TMP_ID = 1

    query = f"INSERT INTO `tabCustomer Dict Catalog`(name, creation, owner, \
        term_customer, section, work_type, materials_group, term_worker, contragent_id, price_customer, price_worker, price_contragent) " \
        "VALUES(%s,%s,%s, %s,%s,%s,%s,%s,%s,%s,%s,%s)"

    for task in excel_data:
        section_name = task["name"]
        name_col, _, price_col = findColumns(task["naming"])
        for inner_task in task["inner_tasks"]:
            ID = proj_name + "-TASK-" + str(TMP_ID)
            name_custoner = inner_task[name_col]
            if price_col is None:
                price_customer = 0.0
            else:
                price_customer = inner_task[price_col]
            data = [ID, "2021-05-25 08:02:14.204645", "Administrator",
                    name_custoner, section_name, "", "", "", 0, price_customer, 0, 0]
            cur.execute(query, data)
            conn.commit()
            TMP_ID += 1
            print(cur.rowcount, "Record inserted successfully into Laptop table")


def renameTasksInProject(cur, proj_name):
    cur.execute(f"select subject, price from tabTask where project = %s", [proj_name])
    task_names_prices = [(item[0], item[1]) for item in cur.fetchall()]
    #print(task_names_prices)
    cur.execute(f"select term_customer, term_worker, price_worker from `tabCustomer Dict Catalog`", [])
    termsDict = cur.fetchall()
    #print(termsDict)

    for name_price in task_names_prices:
        for dictItems in termsDict:
            # if dictItems[1] != "":
            #     print(dictItems)
            if dictItems[0] == name_price[0]:
                # print(termsPair[0], name[0])
                # print(termsPair[1] == "")
                # print(termsPair[0], name[1], ":::", termsPair[1])
                if dictItems[1] != '': # если термин рабочей единицы заполнен для термина заказчика
                    print("найдено совпадение в словаре:", dictItems[0], "->", dictItems[1])                
                    cur.execute(f"update tabTask set price = %s where subject = %s", [dictItems[2], dictItems[0]]) 
                    cur.execute(f"update tabTask set subject = %s where subject = %s", [dictItems[1], dictItems[0]])
                    conn.commit()
                    print(cur.rowcount, "record(s) affected")
                    break
    # TODO сохранить изменения в структуре, потом писать в бд одной транзакцией

def renameBackTasksInProject(cur, proj_name):
    cur.execute(f"select subject, price from tabTask where project = %s", [proj_name])
    task_names_prices = [(item[0], item[1]) for item in cur.fetchall()]
    #print(task_names_prices)
    cur.execute(f"select term_customer, term_worker, price_worker, price_customer from `tabCustomer Dict Catalog`", [])
    termsDict = cur.fetchall()
    #print(termsDict)

    for name_price in task_names_prices:
        for dictItems in termsDict:
            # if dictItems[1] != "":
            #     print(dictItems)
            if dictItems[1] == name_price[0]:
                # print(termsPair[0], name[0])
                # print(termsPair[1] == "")
                # print(termsPair[0], name[1], ":::", termsPair[1])
                if dictItems[0] != '': # если термин рабочей единицы заполнен для термина заказчика
                    print("найдено совпадение в словаре:", dictItems[1], "->", dictItems[0])
                    cur.execute(f"update tabTask set price = %s where subject = %s", [dictItems[3], dictItems[1]])
                    cur.execute(f"update tabTask set subject = %s where subject = %s", [dictItems[0], dictItems[1]])
                    conn.commit()
                    print(cur.rowcount, "record(s) affected")
                    break


def printColumns(cur):
    cur.execute("select * from `tabCustomer Dict Catalog`")

    result = cur.fetchall()
    num_fields = len(cur.description)
    field_names = [i[0] for i in cur.description]
    # pp(field_names)

    names_str = ""
    for parent_name in field_names:
        # print(parent_name)
        names_str += str(parent_name) + ','

    for i in range(len(field_names)):
        print(f"{field_names[i]:<20} {result[0][i]}")
        data = [result[0][i] for i in range(len(result[0]))]


if __name__ == "__main__":
    conn = openBDConnection()
    if len(sys.argv) != 3:
        print("Ождается название проекта и название файла в качестве аргумента.")
        quit(1)

    project_name = sys.argv[1]
    filename = sys.argv[2]

    try:
        excel_data = get_data_excel(filename)
    except:
        print("Ошибка при открытии файла с данными. Проверьте название и путь.")
        quit(1)


    cursor = conn.cursor()


    insertProject(cursor, project_name)
    insertTasksInProjects(cursor, excel_data, project_name)
    #renameBackTasksInProject(cursor, project_name)
    #renameTasksInProject(cursor, project_name)

    conn.close()
