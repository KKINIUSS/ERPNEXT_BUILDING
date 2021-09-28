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
    await state.update_data(translate="company")
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
        cur.execute("select name, subject_company, subject from tabTask where is_group='1' and project=?", mas)
        await state.update_data(project=mas)
        section_task = cur.fetchall()
        free_work = []
        for i in section_task:
            if(i[1]):
                task_subject = i[1]
            else:
                task_subject = i[2]
            free_work.append([InlineKeyboardButton(text=task_subject, callback_data=i[0])])
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
            await call.message.edit_text(text="Главное меню", reply_markup=worker_menu)
            await worker.job.set()
        elif (str == "Поиск"):
            free_work = [[InlineKeyboardButton(text="Назад", callback_data="Назад")]]
            foreman_btn = InlineKeyboardMarkup(inline_keyboard=free_work)
            await call.message.edit_text("Введите название работы. Нажмите 'Назад', чтобы выйти из поиска", reply_markup=foreman_btn)
            await worker.search.set()
        else:
            data = await state.get_data()
            mas = [str]
            free_work = []
            cur.execute("select name, subject, subject_company from tabTask where parent_task=?", mas)
            task = cur.fetchall()
            for i in task:
                if(i[2]):
                    task_subject = i[2]
                else:
                    task_subject = i[1]
                free_work.append([InlineKeyboardButton(text=task_subject, callback_data=i[0])])
            free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
            foreman_btn = InlineKeyboardMarkup(row_width=1,
                inline_keyboard=free_work,
            )
            cur.execute(f"select subject from tabTask where name='{str}'")
            subject = cur.fetchall()
            await state.update_data(parent_task_name=str, parent_task_subject=subject[0][0])
            await call.message.edit_text(text=f"Работы в разделе {subject[0][0]}", reply_markup=foreman_btn)
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
        cur.execute("select name, subject, subject_company from tabTask where is_group='1' and project=?", mas)
        section_task = cur.fetchall()
        await state.update_data(project=mas)
        free_work = []
        for i in section_task:
            if(i[2]):
                task_subject = i[2]
            else:
                task_subject = i[1]
            free_work.append([InlineKeyboardButton(text=task_subject, callback_data=i[0])])
        free_work.append([InlineKeyboardButton(text="Поиск задачи 🔎", callback_data="Поиск")])
        free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
        foreman_btn = InlineKeyboardMarkup(
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
    await state.update_data(search_query=params)
    cur.execute("select object from tabEmployer where name=?", [message.from_user.id])
    object = cur.fetchall()
    free_work = []
    cur.execute(f"select DISTINCT parent_task from tabTask where is_group='1' and project='{object[0][0]}' and (subject like '{params}' or subject_company like '{params}' and parent_task!=NULL")
    task = cur.fetchall()
    if(task != []):
        if(len(task) <= 49):
            for i in task:
                cur.execute("select subject, subject_company from tabTask where name=?", [i[0]])
                parent = cur.fetchall()
                if(parent[0][1]):
                    task_name = parent[0][1]
                else:
                    task_name = parent[0][0]
                free_work.append([InlineKeyboardButton(text=task_name, callback_data=i[0])])
                free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
            foreman_btn = InlineKeyboardMarkup(row_width=1,
                inline_keyboard=free_work,
            )
            await message.answer("Результаты поиска", reply_markup=foreman_btn)
            await worker.search_task.set()
        else:
            free_work = [[InlineKeyboardButton(text="Назад", callback_data="Назад")]]
            foreman_btn = InlineKeyboardMarkup(row_width=1,
                inline_keyboard=free_work,
            )
            await message.answer("Результатов оказалось слишком много, попробуйте ввести название задачи более точно.",
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
    conn.close()

@dp.callback_query_handler(state=worker.search_task)
async def view_search_task(call: CallbackQuery, state=FSMContext):
    conn = mariadb.connect(
        user=user,
        password=password,
        host=host,
        port=port,
        database=database
    )
    cur = conn.cursor()
    if(call.data == "Назад"):
        conn.commit()
        cur.execute("select telegramidforeman from tabEmployer where telegramid=%s" % call.from_user.id)
        tgid_for = cur.fetchall()
        cur.execute("select object from tabEmployer where telegramid=%s" % tgid_for[0][0])
        proj = cur.fetchall()
        mas = [proj[0][0]]
        cur.execute("select name, subject_company, subject from tabTask where is_group='1' and project=?", mas)
        await state.update_data(project=mas)
        section_task = cur.fetchall()
        free_work = []
        for i in section_task:
            if (i[1]):
                task_subject = i[1]
            else:
                task_subject = i[2]
            free_work.append([InlineKeyboardButton(text=task_subject, callback_data=i[0])])
        free_work.append([InlineKeyboardButton(text="Поиск задачи 🔎", callback_data="Поиск")])
        free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
        foreman_btn = InlineKeyboardMarkup(row_width=1,
                                           inline_keyboard=free_work,
                                           )
        await call.message.edit_text(text="Разделы работ", reply_markup=foreman_btn)
        await worker.section_task.set()
    else:
        conn.commit()
        cur.execute("select object from tabEmployer where name=?", [call.from_user.id])
        object = cur.fetchall()
        data = await state.get_data()
        await state.update_data(search_parent_task=call.data)
        cur.execute(f"select name, subject, subject_company from tabTask where is_group='0' and project='{object[0][0]}' and (subject like '{data.get('search_query')}' or "
                    f"subject_company like '{data.get('search_query')}' and parent_task='{call.data}'")
        task = cur.fetchall()
        free_work = []
        for i in task:
            if(i[2]):
                task_subject = i[2]
            else:
                task_subject = i[1]
            free_work.append([InlineKeyboardButton(text=task_subject, callback_data=i[0])])
        free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
        foreman_btn = InlineKeyboardMarkup(row_width=1,
            inline_keyboard=free_work,
        )
        cur.execute(f"select subject, subject_company from tabTask where name='{call.data}'")
        task_name = cur.fetchall()
        await call.message.edit_text(f"Задачи в разделе {task_name} по запросу {data.get('search_query')}")
        await worker.input_task.set()

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
    cur.execute("select fio, telegramidforeman, foreman, object, phone_number from tabEmployer where telegramid=%s" % tgid)
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
            cur.execute("select telegramidforeman from tabEmployer where telegramid=%s" % call.from_user.id)
            tgid_for = cur.fetchall()
            cur.execute("select object from tabEmployer where telegramid=%s" % tgid_for[0][0])
            proj = cur.fetchall()
            mas = []
            mas.append(proj[0][0])
            cur.execute("select name, subject, subject_company from tabTask where is_group='1' and project=?", mas)
            await state.update_data(project=mas)
            section_task = cur.fetchall()
            free_work = []
            for i in section_task:
                if(i[2]):
                    task_name = i[2]
                else:
                    task_name = i[1]
                free_work.append([InlineKeyboardButton(text=task_name, callback_data=i[0])])
            free_work.append([InlineKeyboardButton(text="Поиск задачи 🔎", callback_data="Поиск")])
            free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
            foreman_btn = InlineKeyboardMarkup(row_width=1,
                                               inline_keyboard=free_work,
                                               )
            await call.message.edit_text("Разделы работ", reply_markup=foreman_btn)
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

@dp.callback_query_handler(state=worker.search_input_task)
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
        conn.commit()
        str = call.data
        data = await state.get_data()
        if (str == "Назад"):
            data = await state.get_data()
            conn.commit()
            cur.execute("select object from tabEmployer where name=?", [call.from_user.id])
            object = cur.fetchall()
            free_work = []
            params = data.get("search_query")
            cur.execute(f"select DISTINCT parent_task from tabTask where is_group='1' and project='{object[0][0]}' "
                        f"and (subject like '{params}' or subject_company like '{params}' and parent_task!=''")
            task = cur.fetchall()
            for i in task:
                cur.execute("select subject, subject_company from tabTask where name=?", [i[0]])
                parent = cur.fetchall()
                if (parent[0][1]):
                    task_name = parent[0][1]
                else:
                    task_name = parent[0][0]
                free_work.append([InlineKeyboardButton(text=task_name, callback_data=i[0])])
                free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
            foreman_btn = InlineKeyboardMarkup(row_width=1,
                                               inline_keyboard=free_work,
                                               )
            await call.message.edit_text("Результаты поиска", reply_markup=foreman_btn)
            await worker.search_task.set()
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
            await worker.search_reg_report.set()
    conn.close()

@dp.message_handler(state=worker.search_reg_report)
async def search_reg_report(message: Message, state=FSMContext):
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
    cur.execute(
        "select fio, telegramidforeman, foreman, object, phone_number from tabEmployer where telegramid=%s" % tgid)
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
        cur.execute(
            "select fio, phone_number, telegramid, foreman, dateobj, telegramidforeman, payments from tabEmployer where telegramid=%s" % tgid)
        a = cur.fetchall()
        cur.execute("select phone_number from tabEmployer where telegramid=%s" % a[0][5])
        phone_foreman = cur.fetchall()
        mas = [datetime.datetime.now(), data.get("task_name"), st, datetime.datetime.now(), "Administrator",
               data.get("task_subject"), data.get("parent_task_subject"), "", mes, a[0][0],
               tgid, a[0][1], a[0][3], a[0][5], phone_foreman[0][0], now, 'На рассмотрении', a[0][6]]
        cur.execute("insert into `tabWorker report` (modified, task_name, name ,creation ,owner, "
                    "job, job_section, photo, job_value, worker_name, telegramid, phone_number, foreman_name, telegramidforeman, phone_number_foreman, date, status, payments)"
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", mas)
        conn.commit()
        await message.answer("Ваш отчёт направлен прорабу")
        name_parent = [data.get("task_name")]
        cur.execute("select parent_task from tabTask where name=?", name_parent)
        name1 = cur.fetchall()
        cur.execute(f"select object from tabEmployer where name='{message.from_user.id}'")
        object = cur.fetchall()
        parent_task_mas = [name1[0][0]]
        free_work = []
        params = data.get("search_query")
        cur.execute(f"select name from tabTask where is_group='1' and project={object[0][0]} and (subject like '{params}' or subject_company like '{params}' and parent_task={data.get('search_parent_task')}")
        task = cur.fetchall()
        for i in task:
            cur.execute("select subject, subject_company from tabTask where name=?", [i[0]])
            parent = cur.fetchall()
            if (parent[0][1]):
                task_name = parent[0][1]
            else:
                task_name = parent[0][0]
            free_work.append([InlineKeyboardButton(text=task_name, callback_data=i[0])])
            free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
        foreman_btn = InlineKeyboardMarkup(row_width=1,
                                           inline_keyboard=free_work,
                                           )
        cur.execute(f"select subject, subject_company from tabTask where name={data.get('search_parent_name')}")
        parent = cur.fetchall()
        if(parent[0][1]):
            task_name = parent[0][1]
        else:
            task_name = parent[0][0]
        await message.answer(f"Результаты поиска в разделе {task_name} по запросу {data.get('search_query')}", reply_markup=foreman_btn)
        await worker.search_input_task.set()
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
        free_work = []
        cur.execute("select name, subject, subject_company  from tabTask where parent_task=?", parent_task_mas)
        task = cur.fetchall()
        for i in task:
            if(i[2]):
                task_name = i[2]
            else:
                task_name = i[1]
            free_work.append([InlineKeyboardButton(text=task_name, callback_data=i[0])])
        free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
        foreman_btn = InlineKeyboardMarkup(row_width=1,
            inline_keyboard=free_work,
        )
        cur.execute("select subject from tabTask where name=?", parent_task_mas)
        subject = cur.fetchall()
        await state.update_data(parent_task_name=parent_task_mas, parent_task_subject=subject[0][0])
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

