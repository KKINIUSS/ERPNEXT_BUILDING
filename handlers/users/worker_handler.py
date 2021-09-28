from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from loader import dp
from aiogram.dispatcher import FSMContext
import datetime
from keyboards.default.worker_job import worker_start_job
from states.worker import worker
from keyboards.inline.worker import worker_menu, worker_menu_company
from keyboards.default.worker_no_job import worker_no_job
import mariadb
from data.config import user, password, host, port, database

subject_task = ""
parent_task = ""
@dp.message_handler(state=worker.start_job)
async def join_session(message: Message, state=FSMContext):
    conn = mariadb.connect(
        user=user,
        password=password,
        host=host,
        port=port,
        database=database
    )
    cur = conn.cursor()
    tgid = message.from_user.id
    cur.execute("select fio, telegramidforeman, foreman, object, phone_number from tabEmployer where telegramid=%s" %tgid)
    name = cur.fetchall()
    if(not name):
        await message.answer("Вас еще не взяли на работу", reply_markup=worker_no_job)
        await worker.no_job.set()
    else:
        await state.update_data(telegramid=tgid, name_worker=name[0][0], name_foreman=name[0][2], telegramidforeman=name[0][1], object=name[0][3], phone_number=name[0][4])
        cur.execute("select phone_number from tabEmployer where telegramid=%s" %name[0][1])
        a = cur.fetchall()
        await state.update_data(phone_number_foreman=a[0][0])
        now = datetime.datetime.now()
        await message.answer("Добрый день, сегодня %s число." %now.strftime("%d-%m-%Y"), reply_markup=worker_menu)
        await worker.job.set()
    conn.close()

@dp.callback_query_handler(text_contains="serv:Перевести в термины компании", state=worker.job)
async def translate(call: CallbackQuery, state=FSMContext):
    await state.update_data(translate="company")
    await call.message.edit_text("Меню", reply_markup=worker_menu_company)


@dp.callback_query_handler(text_contains="serv:Перевести в термины заказчика", state=worker.job)
async def translate(call: CallbackQuery, state=FSMContext):
    await state.update_data(translate="customer")
    await call.message.edit_text("Меню", reply_markup=worker_menu)


@dp.callback_query_handler(text_contains="serv:Сделать отчет", state=worker.job)
async def work(call: CallbackQuery, state=FSMContext):
    conn = mariadb.connect(
        user=user,
        password=password,
        host=host,
        port=port,
        database=database
    )
    cur = conn.cursor()
    conn.commit()
    tgid = call.from_user.id
    cur.execute("select fio, telegramidforeman, foreman, object, phone_number from tabEmployer where telegramid=%s" % tgid)
    name = cur.fetchall()
    if (not name):
        await call.message.answer("Вас еще не взяли на работу", reply_markup=worker_no_job)
        await worker.no_job.set()
    else:
        data = await state.get_data()
        conn.commit()
        cur.execute("select telegramidforeman from tabEmployer where telegramid=%s" %call.from_user.id)
        tgid_for = cur.fetchall()
        cur.execute("select object from tabEmployer where telegramid=%s" %tgid_for[0][0])
        proj = cur.fetchall()
        mas = [proj[0][0]]
        cur.execute("select name from tabTask where is_group='1' and project=?", mas)
        await state.update_data(project=mas)
        section_task = cur.fetchall()
        if(data.get("translate") == "customer"):
            free_work = []
            for i in section_task:
                name_mas = [i[0]]
                cur.execute("select term_customer from `tabDictionary reference book` where name=?", name_mas)
                parent = cur.fetchall()
                free_work.append([InlineKeyboardButton(text=parent[0][0], callback_data=i[0])])
            free_work.append([InlineKeyboardButton(text="Поиск задачи 🔎", callback_data="Поиск")])
            free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
            foreman_btn = InlineKeyboardMarkup(row_width=1,
                inline_keyboard=free_work,
            )
        else:
            free_work = []
            for i in section_task:
                name_mas = [i[0]]
                cur.execute("select term_customer, term_worker from `tabDictionary reference book` where name=?", name_mas)
                parent = cur.fetchall()
                if(parent[0] != "" ):
                    if (parent[0][1] != ""):
                        free_work.append([InlineKeyboardButton(text=parent[0][1], callback_data=i[0])])
                    else:
                        free_work.append([InlineKeyboardButton(text=parent[0][0], callback_data=i[0])])
            free_work.append([InlineKeyboardButton(text="Поиск задачи 🔎", callback_data="Поиск")])
            free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
            foreman_btn = InlineKeyboardMarkup(row_width=1,
                inline_keyboard=free_work,
            )
        await call.message.edit_text(text="Разделы работ", reply_markup=foreman_btn)
        await worker.section_task.set()
    conn.close()
@dp.callback_query_handler(state=worker.section_task)
async def work(call: CallbackQuery, state=FSMContext):
    conn = mariadb.connect(
        user=user,
        password=password,
        host=host,
        port=port,
        database=database
    )
    cur = conn.cursor()
    conn.commit()
    tgid = call.from_user.id
    data = await state.get_data()
    cur.execute("select fio, telegramidforeman, foreman, object, phone_number from tabEmployer where telegramid=%s" % tgid)
    name = cur.fetchall()
    if (not name):
        await call.message.answer("Вас еще не взяли на работу", reply_markup=worker_no_job)
        await worker.no_job.set()
    else:
        conn.commit()
        str = call.data
        if (str == "Назад"):
            if(data.get("translate") == "customer"):
                await call.message.edit_text(text="Главное меню", reply_markup=worker_menu)
            else:
                await call.message.edit_text(text="Главное меню", reply_markup=worker_menu_company)
            await worker.job.set()
        elif (str == "Поиск"):
            free_work = [[InlineKeyboardButton(text="Назад", callback_data="Назад")]]
            foreman_btn = InlineKeyboardMarkup(inline_keyboard=free_work)
            await call.message.edit_text("Введите название работы. Нажмите 'Назад', чтобы выйти из поиска", reply_markup=foreman_btn)
            await worker.search.set()
        else:
            data = await state.get_data()
            if(data.get("translate") == "customer"):
                mas = [str]
                free_work = []
                cur.execute("select subject, name from tabTask where parent_task=?", mas)
                task = cur.fetchall()
                for i in task:
                    mas1 = [i[1]]
                    cur.execute("select term_customer from `tabDictionary reference book` where name=?", mas1)
                    term_customer = cur.fetchall()
                    free_work.append([InlineKeyboardButton(text=term_customer[0][0], callback_data=i[1])])
                free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
                foreman_btn = InlineKeyboardMarkup(row_width=1,
                    inline_keyboard=free_work,
                )
            else:
                mas = [str]
                free_work = []
                cur.execute("select subject, name from tabTask where parent_task=?", mas)
                task = cur.fetchall()
                for i in task:
                    mas1 = [i[1]]
                    cur.execute("select term_customer, term_worker from `tabDictionary reference book` where name=?", mas1)
                    term_customer = cur.fetchall()
                    if(term_customer[0][1]):
                        free_work.append([InlineKeyboardButton(text=term_customer[0][1], callback_data=i[1])])
                    else:
                        free_work.append([InlineKeyboardButton(text=term_customer[0][0], callback_data=i[1])])
                free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
                foreman_btn = InlineKeyboardMarkup(row_width=1,
                    inline_keyboard=free_work,
                )
            cur.execute("select subject from tabTask where name='%s'" %str)
            subject = cur.fetchall()
            await state.update_data(parent_task_name=str, parent_task_subject=subject[0][0])
            await call.message.edit_text(text="Работы в разделе %s" %subject[0][0], reply_markup=foreman_btn)
            await worker.input_task.set()
    conn.close()

@dp.callback_query_handler(state=worker.search)
async def back_search(call: CallbackQuery, state=FSMContext):
    conn = mariadb.connect(
        user=user,
        password=password,
        host=host,
        port=port,
        database=database
    )
    cur = conn.cursor()
    if(call.data == 'Назад'):
        data = await state.get_data()
        conn.commit()
        cur.execute("select telegramidforeman from tabEmployer where telegramid=%s" % call.from_user.id)
        tgid_for = cur.fetchall()
        cur.execute("select object from tabEmployer where telegramid=%s" % tgid_for[0][0])
        proj = cur.fetchall()
        mas = [proj[0][0]]
        cur.execute("select name from tabTask where is_group='1' and project=?", mas)
        await state.update_data(project=mas)
        section_task = cur.fetchall()
        if (data.get("translate") == "customer"):
            free_work = []
            for i in section_task:
                name_mas = [i[0]]
                cur.execute("select term_customer from `tabDictionary reference book` where name=?", name_mas)
                parent = cur.fetchall()
                free_work.append([InlineKeyboardButton(text=parent[0][0], callback_data=i[0])])
            free_work.append([InlineKeyboardButton(text="Поиск задачи 🔎", callback_data="Поиск")])
            free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
            foreman_btn = InlineKeyboardMarkup(
                inline_keyboard=free_work,
            )
        else:
            free_work = []
            for i in section_task:
                name_mas = [i[0]]
                cur.execute("select term_customer, term_worker from `tabDictionary reference book` where name=?", name_mas)
                parent = cur.fetchall()
                if (parent[0] != ""):
                    if (parent[0][1] != ""):
                        free_work.append([InlineKeyboardButton(text=parent[0][1], callback_data=i[0])])
                    else:
                        free_work.append([InlineKeyboardButton(text=parent[0][0], callback_data=i[0])])
            free_work.append([InlineKeyboardButton(text="Поиск задачи 🔎", callback_data="Поиск")])
            free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
            foreman_btn = InlineKeyboardMarkup(row_width=1,
                inline_keyboard=free_work,
            )
        await call.message.edit_text(text="Разделы работ", reply_markup=foreman_btn)
        await worker.section_task.set()
    conn.close()

@dp.message_handler(state=worker.search)
async def search_show(message: Message, state=FSMContext):
    conn = mariadb.connect(
        user=user,
        password=password,
        host=host,
        port=port,
        database=database
    )
    cur = conn.cursor()
    params = "%" + message.text + "%"
    data = await state.get_data()
    cur.execute("select object from tabEmployer where name=?", [message.from_user.id])
    object = cur.fetchall()
    if (data.get("translate") == "customer"):
        free_work = []
        cur.execute("select subject, name, parent_task from tabTask where is_group='0' and project='%s' and subject like '%s'" %(object[0][0], params))
        task = cur.fetchall()
        if(task != []):
            if(len(task) <= 49):
                for i in task:
                    cur.execute("select term_customer from `tabDictionary reference book` where name=?", [i[1]])
                    term_customer = cur.fetchall()
                    cur.execute("select subject from tabTask where name=?", [i[2]])
                    parent = cur.fetchall()
                    free_work.append([InlineKeyboardButton(text=f"[{parent[0][0]}]" + term_customer[0][0], callback_data=i[1])])
                    free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
                foreman_btn = InlineKeyboardMarkup(row_width=1,
                    inline_keyboard=free_work,
                )
                await message.answer("Результаты поиска", reply_markup=foreman_btn)
                await worker.input_task.set()
            else:
                free_work = [[InlineKeyboardButton(text="Назад", callback_data="Назад")]]
                foreman_btn = InlineKeyboardMarkup(row_width=1,
                    inline_keyboard=free_work,
                )
                await message.answer(
                    "Результатов оказалось слишком много, попробуйте ввести название задачи более точно.",
                    reply_markup=foreman_btn)
                await worker.search.set()
        else:
            free_work = [[InlineKeyboardButton(text="Назад", callback_data="Назад")]]
            foreman_btn = InlineKeyboardMarkup(row_width=1,
                inline_keyboard=free_work,
            )
            await message.answer("Нет результатов, попробуйте ввести название задачи более точно.",
                                 reply_markup=foreman_btn)
            await worker.search.set()
    else:
        free_work = []
        cur.execute("select subject, name, parent_task from tabTask where is_group='0' and project='%s' and subject like '%s'" %(object[0][0], params))
        task = cur.fetchall()
        if(task != []):
            if(len(task) <= 49):
                for i in task:
                    print(i)
                    cur.execute("select term_customer, term_worker from `tabDictionary reference book` where name=?", [i[1]])
                    term_customer = cur.fetchall()
                    cur.execute("select subject from tabTask where name=?", [i[2]])
                    parent = cur.fetchall()
                    if (term_customer[0][1]):
                        free_work.append([InlineKeyboardButton(text=f"[{parent[0][0]}]" + term_customer[0][1], callback_data=i[1])])
                    else:
                        free_work.append([InlineKeyboardButton(text=f"[{parent[0][0]}]" + term_customer[0][0], callback_data=i[1])])
                free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
                foreman_btn = InlineKeyboardMarkup(row_width=1,
                    inline_keyboard=free_work,
                )
                await message.answer("Результаты поиска", reply_markup=foreman_btn)
                await worker.input_task.set()
            else:
                free_work = [[InlineKeyboardButton(text="Назад", callback_data="Назад")]]
                foreman_btn = InlineKeyboardMarkup(row_width=1,
                    inline_keyboard=free_work,
                )
                await message.answer("Результатов оказалось слишком много, попробуйте ввести название задачи более точно.", reply_markup=foreman_btn)
                await worker.search.set()
        else:
            free_work = [[InlineKeyboardButton(text="Назад", callback_data="Назад")]]
            foreman_btn = InlineKeyboardMarkup(row_width=1,
                inline_keyboard=free_work,
            )
            await message.answer("Нет результатов, попробуйте ввести название задачи более точно.", reply_markup=foreman_btn)
            await worker.search.set()
    conn.close()

@dp.callback_query_handler(state=worker.input_task)
async def work(call: CallbackQuery, state=FSMContext):
    conn = mariadb.connect(
        user=user,
        password=password,
        host=host,
        port=port,
        database=database
    )
    cur = conn.cursor()
    conn.commit()
    tgid = call.from_user.id
    cur.execute(
        "select fio, telegramidforeman, foreman, object, phone_number from tabWorker where telegramid=%s" % tgid)
    name = cur.fetchall()
    if (not name):
        await call.message.answer("Вас еще не взяли на работу", reply_markup=worker_no_job)
        await worker.no_job.set()
    else:
        conn.commit()
        str = call.data
        data = await state.get_data()
        if (str == "Назад"):
            data = await state.get_data()
            conn.commit()
            print(21)
            cur.execute("select telegramidforeman from tabWorker where telegramid=%s" % call.from_user.id)
            tgid_for = cur.fetchall()
            cur.execute("select object from tabProrab where telegramid=%s" % tgid_for[0][0])
            proj = cur.fetchall()
            print(proj)
            mas = []
            mas.append(proj[0][0])
            print(mas)
            cur.execute("select name from tabTask where is_group='1' and project=?", mas)
            await state.update_data(project=mas)
            section_task = cur.fetchall()
            print(data.get("translate"))
            if (data.get("translate") == "customer"):
                free_work = []
                for i in section_task:
                    name_mas = []
                    name_mas.append(i[0])
                    cur.execute("select term_customer from `tabDictionary reference book` where name=?", name_mas)
                    parent = cur.fetchall()
                    free_work.append([InlineKeyboardButton(text=parent[0][0], callback_data=i[0])])
                free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
                foreman_btn = InlineKeyboardMarkup(row_width=1,
                    inline_keyboard=free_work,
                )
            else:
                free_work = []
                for i in section_task:
                    name_mas = []
                    name_mas.append(i[0])
                    cur.execute("select term_customer, term_worker from `tabDictionary reference book` where name=?",
                                name_mas)
                    parent = cur.fetchall()
                    print(parent)
                    if (parent[0] != ""):
                        if (parent[0][1] != ""):
                            free_work.append([InlineKeyboardButton(text=parent[0][1], callback_data=i[0])])
                        else:
                            free_work.append([InlineKeyboardButton(text=parent[0][0], callback_data=i[0])])
                free_work.append([InlineKeyboardButton(text="Поиск задачи 🔎", callback_data="Поиск")])
                free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
                foreman_btn = InlineKeyboardMarkup(row_width=1,
                    inline_keyboard=free_work,
                )
            await call.message.edit_text(text="Разделы работ", reply_markup=foreman_btn)
            await worker.section_task.set()
        else:
            cur.execute("select subject from tabTask where name='%s'" % str)
            task_name = cur.fetchall()
            await state.update_data(task_name=str, task_subject=task_name[0][0])
            free_work = []
            free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
            foreman_btn = InlineKeyboardMarkup(row_width=1,
                inline_keyboard=free_work,
            )
            await call.message.edit_text(text="Введите объем выполненной работы")
            await worker.reg_report.set()
    conn.close()

@dp.message_handler(state=worker.reg_report)
async def free_work(message: Message, state=FSMContext):
    conn = mariadb.connect(
        user=user,
        password=password,
        host=host,
        port=port,
        database=database
    )
    cur = conn.cursor()
    conn.commit()
    tgid = message.from_user.id
    cur.execute("select fio, telegramidforeman, foreman, object, phone_number from tabEmployer where telegramid=%s" % tgid)
    name = cur.fetchall()
    if (not name):
        await message.answer("Вас еще не взяли на работу", reply_markup=worker_no_job)
        await worker.no_job.set()
    else:
        conn.commit()
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        data = await state.get_data()
        mes = message.text
        st = str(datetime.datetime.now()) + " " + str(data.get("task_name") + " " + str(tgid))
        cur.execute("select fio, phone_number, telegramid, foreman, dateobj, telegramidforeman, payments from tabEmployer where telegramid=%s" %tgid)
        a = cur.fetchall()
        cur.execute("select phone_number from tabEmployer where telegramid=%s" %a[0][5])
        phone_foreman = cur.fetchall()
        mas = [datetime.datetime.now(), data.get("task_name"), st, datetime.datetime.now(), "Administrator", data.get("task_subject"), data.get("parent_task_subject"), "", mes, a[0][0],
               tgid, a[0][1], a[0][3], a[0][5], phone_foreman[0][0], now, 'На рассмотрении', a[0][6]]
        cur.execute("insert into `tabWorker report` (modified, task_name, name ,creation ,owner, "
                    "job, job_section, photo, job_value, worker_name, telegramid, phone_number, foreman_name, telegramidforeman, phone_number_foreman, date, status, payments)"
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", mas)
        conn.commit()
        await message.answer("Ваш отчёт направлен прорабу")
        name_parent = [data.get("task_name")]
        cur.execute("select parent_task from tabTask where name=?", name_parent )
        name1 = cur.fetchall()
        parent_task_mas = [name1[0][0]]
        cur.execute("select subject, name from tabTask where parent_task=?", parent_task_mas )
        if (data.get("translate") == "customer"):
            free_work = []
            cur.execute("select subject, name from tabTask where parent_task=?", parent_task_mas)
            task = cur.fetchall()
            for i in task:
                cur.execute("select term_customer from `tabDictionary reference book` where name=?", [i[1]])
                term_customer = cur.fetchall()
                free_work.append([InlineKeyboardButton(text=term_customer[0][0], callback_data=i[1])])
            free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
            foreman_btn = InlineKeyboardMarkup(row_width=1,
                inline_keyboard=free_work,
            )
        else:
            free_work = []
            cur.execute("select subject, name from tabTask where parent_task=?", parent_task_mas)
            task = cur.fetchall()
            for i in task:
                cur.execute("select term_customer, term_worker from `tabDictionary reference book` where name=?", [i[1]])
                term_customer = cur.fetchall()
                if (term_customer[0][1]):
                    free_work.append([InlineKeyboardButton(text=term_customer[0][1], callback_data=i[1])])
                else:
                    free_work.append([InlineKeyboardButton(text=term_customer[0][0], callback_data=i[1])])
            free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
            foreman_btn = InlineKeyboardMarkup(row_width=1,
                inline_keyboard=free_work,
            )
        cur.execute("select subject from tabTask where name=?", parent_task_mas)
        subject = cur.fetchall()
        await state.update_data(parent_task_name=str, parent_task_subject=subject[0][0])
        await message.answer(text="Работы в разделе %s" % subject[0][0], reply_markup=foreman_btn)
        await worker.input_task.set()
    conn.close()

@dp.callback_query_handler(text_contains="serv:Закончить рабочий день", state=worker.job)
async def end_session(call: CallbackQuery, state=FSMContext):
    conn = mariadb.connect(
        user=user,
        password=password,
        host=host,
        port=port,
        database=database
    )
    cur = conn.cursor()
    conn.commit()
    tgid = call.from_user.id
    cur.execute("select fio, telegramidforeman, foreman, object, phone_number from tabEmployer where telegramid=%s" % tgid)
    name = cur.fetchall()
    if (not name):
        await call.message.answer("Вас еще не взяли на работу", reply_markup=worker_no_job)
        await worker.no_job.set()
    else:
        cur.execute("update tabEmployer set activity='0' where name=?", [call.from_user.id])
        conn.commit()
        mas = [datetime.datetime.now().strftime('%Y-%m-%d'), datetime.datetime.now().strftime('%Y-%m-%d'), call.from_user.id]
        mes = [datetime.datetime.now().strftime('%Y-%m-%d'), tgid]
        cur.execute("select * from `tabWorker activity` where date_join=? and telegramid=?", mes)
        a = cur.fetchall()
        if(a):
            cur.execute("update `tabWorker activity` set date_end=? where date_join=? and telegramid=?", mas)
            conn.commit()
            await call.message.delete()
            await call.message.answer(text="Вы закончили рабочий день", reply_markup=worker_start_job)
            await state.finish()
        else:
            cur.execute("delete from `tabWorker activity temp` where telegramid=%s" %tgid)
            conn.commit()
            await call.message.delete()
            await call.message.answer(text="Вы закончили рабочий день", reply_markup=worker_start_job)
            await state.finish()
    conn.close()

