from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from loader import dp
from aiogram.dispatcher import FSMContext
from keyboards.default.foreman_job import foreman_start_job
from database.connect_db import conn, cur, cur1
import datetime
from loader import bot
from states.foreman import foreman
from keyboards.inline.foreman_menu import foreman_menu
import mariadb
from data.config import user, password, host, port, database

@dp.message_handler(text="Начать рабочий день", state=foreman.start_job)
async def join_session(message: Message):
    now = datetime.datetime.now()
    await message.answer("Добрый день, сегодня %s число." %now.strftime("%d-%m-%Y"), reply_markup=foreman_menu)
    await foreman.job.set()


@dp.callback_query_handler(text_contains="serv:Журнал учёта рабочих", state=foreman.job)
async def check_time(call: CallbackQuery, state=FSMContext):
    conn = mariadb.connect(
        user=user,
        password=password,
        host=host,
        port=port,
        database=database
    )
    cur = conn.cursor()
    cur.execute("select fio, telegramid from `tabWorker activity temp` where telegramidforeman=%s" %call.from_user.id)
    a = cur.fetchall()
    free_work = []
    for i in a:
        free_work.append([InlineKeyboardButton(text=i[0], callback_data=i[1])])
    free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
    foreman_btn = InlineKeyboardMarkup(
        inline_keyboard=free_work,
    )
    await call.message.edit_text(text="Список отметившихся", reply_markup=foreman_btn)
    conn.close()
    await foreman.activity_worker.set()

@dp.callback_query_handler(state=foreman.activity_worker)
async def free_work(call: CallbackQuery, state=FSMContext):
    conn = mariadb.connect(
        user=user,
        password=password,
        host=host,
        port=port,
        database=database
    )
    cur = conn.cursor()
    conn.commit()
    str = call.data
    if (str == "Назад"):
        await call.message.edit_text(text="Главное меню", reply_markup=foreman_menu)
        await foreman.job.set()
    else:
        cur.execute("select fio, date_join, telegramidforeman, name from `tabWorker activity temp` where telegramid=%s" % str)
        a = cur.fetchall()
        cur.execute("select phone_number from tabEmployer where telegramid=%s" % str)
        tg = cur.fetchall()
        free_work = []
        time_work = ""
        time_work = a[0][1]
        free_work.append([InlineKeyboardButton(text="Принять", callback_data="Принять")])
        free_work.append([InlineKeyboardButton(text="Отклонить", callback_data="Отклонить")])
        free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
        foreman_choise_free_btn = InlineKeyboardMarkup(
            inline_keyboard=free_work,
        )
        print(a[0][1])
        await call.message.edit_text("Имя рабочего %s\nНомер телефона: %s\nВремя прихода на работу: %s"
                                     %(a[0][0], tg[0][0], time_work),reply_markup=foreman_choise_free_btn)
        await state.update_data(telegramid=str, fio=a[0][0], date_join=a[0][1], telegramidforeman=a[0][2], nameTaskActivity=a[0][3])
        await foreman.activity_worker_profile.set()
    conn.close()

@dp.callback_query_handler(state=foreman.activity_worker_profile)
async def invite_team(call: CallbackQuery, state=FSMContext):
    conn = mariadb.connect(
        user=user,
        password=password,
        host=host,
        port=port,
        database=database
    )
    cur = conn.cursor()
    conn.commit()
    stri = call.data
    telegram = call.from_user.id
    if (stri == "Назад"):
        cur.execute(
            "select fio, telegramid from `tabWorker activity temp` where telegramidforeman=%s" % call.from_user.id)
        a = cur.fetchall()
        free_work = []
        print(a)
        for i in a:
            free_work.append([InlineKeyboardButton(text=i[0], callback_data=i[1])])
        free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
        foreman_btn = InlineKeyboardMarkup(
            inline_keyboard=free_work,
        )
        await call.message.edit_text(text="Список отметившихся", reply_markup=foreman_btn)
        await foreman.activity_worker.set()
    elif(stri == "Принять"):
        mas_foreman = []
        now = datetime.datetime.now()
        data = await state.get_data()
        print(telegram)
        mas = []
        st = ""
        mas.append(data.get("nameTaskActivity"))
        mas.append(datetime.datetime.now())
        mas.append("Administrator")
        mas.append(data.get("fio"))
        mas.append(data.get("date_join"))
        mas.append(None)
        mas.append(data.get("telegramid"))
        mas.append(data.get("telegramidforeman"))
        cur.execute(
            "insert into `tabWorker activity` (name ,creation ,owner, fio, date_join, date_end, telegramid, telegramidforeman)"
            " VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", mas)
        mas = []
        mas.append(data.get("telegramid"))
        mas.append(data.get("date_join"))
        cur.execute("delete from `tabWorker activity temp` where telegramid=? and date_join=?", mas)
        conn.commit()
        cur.execute(
            "select fio, telegramid from `tabWorker activity temp` where telegramidforeman=%s" % call.from_user.id)
        a = cur.fetchall()
        free_work = []
        await call.message.delete()
        await call.message.answer("Принято!")
        print(a)
        for i in a:
            free_work.append([InlineKeyboardButton(text=i[0], callback_data=i[1])])
        free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
        foreman_btn = InlineKeyboardMarkup(
            inline_keyboard=free_work,
        )
        await call.message.answer(text="Список отметившихся", reply_markup=foreman_btn)
        await foreman.activity_worker.set()
    elif(stri == "Отклонить"):
        data = await state.get_data()
        temp = []
        print(data.get("telegramid"))
        j = data.get("telegramid")
        j = int(j)
        await bot.send_message(j, "Сообщение от прораба: "
                                  "Ваш данные начала работы отклонены!")
        mes = []
        mes.append(data.get("date_join"))
        mes.append(data.get("telegramid"))
        cur.execute("delete from `tabWorker activity temp` where date_join=? and telegramid=?", mes)
        conn.commit()
        await call.message.delete()
        await call.message.answer("Отклонено!")
        cur.execute(
            "select fio, telegramid from `tabWorker activity temp` where telegramidforeman=%s" % call.from_user.id)
        a = cur.fetchall()
        free_work = []
        print(a)
        for i in a:
            free_work.append([InlineKeyboardButton(text=i[0], callback_data=i[1])])
        free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
        foreman_btn = InlineKeyboardMarkup(
            inline_keyboard=free_work,
        )
        await call.message.answer(text="Список отметившихся", reply_markup=foreman_btn)
        await foreman.activity_worker.set()
    conn.close()


@dp.callback_query_handler(text_contains="serv:Список подчиненных", state=foreman.job)
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
    cur.execute("select fio, telegramid from tabEmployer where status='Подтвержден' and telegramidforeman=%s" %call.from_user.id)
    a = cur.fetchall()
    free_work = []
    print(a)
    for i in a:
        free_work.append([InlineKeyboardButton(text=i[0], callback_data=i[1])])
    free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
    foreman_btn = InlineKeyboardMarkup(
        inline_keyboard=free_work,
    )
    await call.message.edit_text(text="Список подчиненных", reply_markup=foreman_btn)
    await foreman.worker.set()
    conn.close()

@dp.callback_query_handler(state=foreman.worker)
async def free_work(call: CallbackQuery, state=FSMContext):
    conn = mariadb.connect(
        user=user,
        password=password,
        host=host,
        port=port,
        database=database
    )
    cur = conn.cursor()
    conn.commit()
    str = call.data
    if (str == "Назад"):
        await call.message.edit_text(text="Главное меню", reply_markup=foreman_menu)
        await foreman.job.set()
    else:
        cur.execute("select fio, phone_number, telegramid, comments_foreman, photo_worker, photo_passport from tabEmployer where status='Подтвержден' and telegramid=%s" % str)
        a = cur.fetchall()
        free_work = []
        #free_work.append([InlineKeyboardButton(text="Удалить", callback_data="Удалить")])
        free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
        foreman_choise_free_btn = InlineKeyboardMarkup(
            inline_keyboard=free_work,
        )
        await call.message.edit_text("Профиль рабочего %s\nНомер телефона: %s\nТелеграм ID: %s\nКомментарий предыдущего прораба: %s\n" %(a[0][0], a[0][1], a[0][2], a[0][3]),
                                     reply_markup=foreman_choise_free_btn)
        await state.update_data(fio=a[0][0], phone_number=a[0][1], telegramid=a[0][2], comment=a[0][3], photo=a[0][4], passport=a[0][5])
        await foreman.worker_profile.set()
    conn.close()

@dp.callback_query_handler(state=foreman.worker_profile)
async def invite_team(call: CallbackQuery, state=FSMContext):
    conn = mariadb.connect(
        user=user,
        password=password,
        host=host,
        port=port,
        database=database
    )
    cur = conn.cursor()
    conn.commit()
    str = call.data
    telegram = call.from_user.id
    if (str == "Назад"):
        cur.execute(
            "select fio, telegramid from tabEmployer where status='Подтвержден' and telegramidforeman=%s" %call.from_user.id)
        a = cur.fetchall()
        free_work = []
        print(a)
        for i in a:
            free_work.append([InlineKeyboardButton(text=i[0], callback_data=i[1])])
        free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
        foreman_btn = InlineKeyboardMarkup(
            inline_keyboard=free_work,
        )
        await call.message.edit_text(text="Список подчиненных", reply_markup=foreman_btn)
        await foreman.worker.set()
    conn.close()

@dp.callback_query_handler(text_contains="serv:Список отчетов", state=foreman.job)
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
    cur.execute("select distinct worker_name, telegramid"
                " from `tabWorker report` where status='На рассмотрении' and telegramidforeman=%s" %call.from_user.id)
    a = cur.fetchall()
    free_work = []
    print(a)
    b = []
    for i in a:
        free_work.append([InlineKeyboardButton(text=i[0] , callback_data=i[1])])
        b.clear()
    free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
    foreman_btn = InlineKeyboardMarkup(
        inline_keyboard=free_work,
    )
    await call.message.edit_text(text="Список отчетов", reply_markup=foreman_btn)
    await foreman.report_temp.set()
    conn.close()

@dp.callback_query_handler(state=foreman.report_temp)
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
    stri = call.data
    if(stri == "Назад"):
        await call.message.edit_text(text="Главное меню", reply_markup=foreman_menu)
        await foreman.job.set()
    else:
        mas_data = [call.from_user.id, stri]
        cur.execute("select job, job_section, photo, job_value, worker_name, telegramid, phone_number, foreman_name, phone_number_foreman, date"
                " from `tabWorker report` where status='На рассмотрении' and telegramidforeman=? and telegramid=?", mas_data)
        a = cur.fetchall()
        mis = [stri]
        cur.execute("select fio from tabEmployer where telegramid=?", mis)
        c = cur.fetchall()
        free_work = []
        print(a)
        for i in a:
            st = str(i[9])
            free_work.append([InlineKeyboardButton(text=i[0] , callback_data=i[5] + "+" + st)])
        free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
        foreman_btn = InlineKeyboardMarkup(
            inline_keyboard=free_work,
        )
        await call.message.edit_text(text="Список отчетов рабочего %s" %c[0][0], reply_markup=foreman_btn)
        await foreman.report_temp_down.set()
    conn.close()

@dp.callback_query_handler(state=foreman.report_temp_down)
async def free_work(call: CallbackQuery, state=FSMContext):
    conn = mariadb.connect(
        user=user,
        password=password,
        host=host,
        port=port,
        database=database
    )
    cur = conn.cursor()
    conn.commit()
    str = call.data
    if (str == "Назад"):
        cur.execute(
            "select distinct worker_name, telegramid"
            " from `tabWorker report` where status='На рассмотрении' and telegramidforeman=%s" % call.from_user.id)
        a = cur.fetchall()
        free_work = []
        for i in a:
            free_work.append([InlineKeyboardButton(text=i[0], callback_data=i[1])])
        free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
        foreman_btn = InlineKeyboardMarkup(
            inline_keyboard=free_work,
        )
        await call.message.edit_text(text="Список отчетов", reply_markup=foreman_btn)
        await foreman.report_temp.set()
    else:
        mas = str.split("+")
        cur.execute("select job, job_section, photo, job_value, worker_name, telegramid, phone_number, "
                    "foreman_name, telegramidforeman, phone_number_foreman, date, task_name, name "
                    "from `tabWorker report` where status='На рассмотрении' and telegramid=? and date=?", mas)
        a = cur.fetchall()
        free_work = []
        free_work.append([InlineKeyboardButton(text="Принять", callback_data="Принять")])
        free_work.append([InlineKeyboardButton(text="Отклонить", callback_data="Отклонить")])
        free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
        foreman_choise_free_btn = InlineKeyboardMarkup(
            inline_keyboard=free_work,
        )
        mis = [a[0][11]]
        cur.execute("select amount, progress_amount from tabTask where name=?", mis )
        b = cur.fetchall()
        print(a)
        await call.message.edit_text("Название работы: %s\nРаздел работы: %s\nОбъем работ: %s\nВыполнено на текущих момент: %s\nОбщий объем работ: %s\nНомер телефона рабочего: %s\nИмя рабочего: %s" %(a[0][0], a[0][1], a[0][3], b[0][1], b[0][0], a[0][6], a[0][4]), reply_markup=foreman_choise_free_btn)
        await state.update_data(job=a[0][0], job_section=a[0][1], telegramid_report=a[0][5],
                                photo_work=a[0][2], job_value=a[0][3],
                                worker_name=a[0][4], phone_number_worker_report=a[0][6],
                                foreman_report_name=a[0][7], telegramid_report_forename=a[0][8],
                                foreman_report_phone_number=a[0][9], date=a[0][10], task_name=a[0][11])
        await foreman.report_temp_profile.set()
    conn.close()

@dp.callback_query_handler(state=foreman.report_temp_profile)
async def invite_team(call: CallbackQuery, state=FSMContext):
    conn = mariadb.connect(
        user=user,
        password=password,
        host=host,
        port=port,
        database=database
    )
    cur = conn.cursor()
    conn.commit()
    stri = call.data
    if (stri == "Назад"):
        data = await state.get_data()
        await state.update_data(telegramid_report=data.get("telegramid_report"))
        temp = [data.get("telegramid_report"), call.from_user.id]
        cur.execute("select job, job_section, photo, job_value, worker_name, telegramid, phone_number, "
                    "foreman_name, phone_number_foreman, date, task_name "
                    "from `tabWorker report` where status='На рассмотрении' and telegramid=? and telegramidforeman=?", temp)
        a = cur.fetchall()
        cur.execute("select fio from tabEmployer where telegramid=%s" % temp[0])
        c = cur.fetchall()
        free_work = []
        for i in a:
            st = i[9]
            st = str(st)
            free_work.append([InlineKeyboardButton(text=i[0], callback_data=i[5] + "+" + st)])
        free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
        foreman_btn = InlineKeyboardMarkup(
            inline_keyboard=free_work,
        )
        await call.message.edit_text(text="Список отчетов рабочего %s" %c[0][0], reply_markup=foreman_btn)
        await foreman.report_temp_down.set()
    elif(stri == "Принять"):
        now = datetime.datetime.now()
        data = await state.get_data()
        await state.update_data(telegramid_report=data.get("telegramid_report"))
        temp=[]
        temp.append(data.get("telegramid_report"))
        temp.append(data.get("date"))
        cur.execute("select job, job_section, photo, job_value, worker_name, telegramid, phone_number, foreman_name, telegramidforeman,"
                    "phone_number_foreman, date, task_name, name from `tabWorker report` where status='На рассмотрении' and telegramid=? and date=?", temp)
        a = cur.fetchall()
        cur.execute(f"update `tabWorker report` set status='Принято' where telegramid=? and date=?", temp)
        conn.commit()
        cur.execute("select amount, progress_amount from tabTask where name=?", [a[0][11]])
        b = cur.fetchall()
        job_value = a[0][3]
        job_max = b[0][0]
        job_current_value = b[0][1]
        if(type(job_current_value) == None):
            job_current_value = 0.
        progress = (float(job_value) / float(job_max)) * 100
        progress_amount = float(job_current_value) + float(job_value)
        mes = [progress_amount, float(progress), a[0][11]]
        cur.execute("update tabTask set progress_amount=?, progress=? where name=?", mes)
        await call.message.delete()
        await call.message.answer("Прогресс по задаче обновлён")
        await call.message.answer("Отчет занесён в базу!")
        conn.commit()
        tempa = [temp[0], call.from_user.id]
        cur.execute("select job, job_section, photo, job_value, worker_name, telegramid, "
                    "phone_number, foreman_name, phone_number_foreman, date from "
                    "`tabWorker report` where status='На рассмотрении' and telegramid=? and telegramidforeman=?", tempa)
        a = cur.fetchall()
        cur.execute("select fio from tabEmployer where telegramid=%s" % temp[0])
        c = cur.fetchall()
        free_work = []
        for i in a:
            free_work.append([InlineKeyboardButton(text=i[0], callback_data=i[5] + "+" + str(a[0][9]))])
        free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
        foreman_btn = InlineKeyboardMarkup(
            inline_keyboard=free_work,
        )
        await call.message.answer(text="Список отчетов рабочего %s" % c[0][0], reply_markup=foreman_btn)
        await foreman.report_temp_down.set()
    elif (stri == "Отклонить"):
        data = await state.get_data()
        await state.update_data(telegramid_report=data.get("telegramid_report"))
        temp = [data.get("telegramid_report"), data.get("date")]
        cur.execute("update `tabWorker report` set status='Отклонен' where telegramid=? and date=?", temp)
        conn.commit()
        #await bot.send_message(data.get("telegramid_report"), "Ваш отчет отклонили!")
        await call.message.delete()
        free_work = []
        free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
        foreman_btn = InlineKeyboardMarkup(inline_keyboard=free_work,)
        await call.message.answer("Пожалуйста, напишите причину отклонения отчёта. \nВы можете нажать `Назад`, чтобы не писать комментарий.", reply_markup=foreman_btn)
        await foreman.cancel_report.set()
    conn.close()

@dp.callback_query_handler(state=foreman.cancel_report)
async def back_to_profile(call: CallbackQuery, state=FSMContext):
    conn = mariadb.connect(
        user=user,
        password=password,
        host=host,
        port=port,
        database=database
    )
    cur = conn.cursor()
    call_back = call.data
    await call.message.answer("Отчёт отклонён")
    if(call_back == "Назад"):
        data = await state.get_data()
        await state.update_data(telegramid_report=data.get("telegramid_report"))
        btn = [[InlineKeyboardButton(text="Понятно", callback_data="Понятно")]]
        bnt_inl = InlineKeyboardMarkup(
            inline_keyboard=btn,
        )
        await bot.send_message(data.get("telegramid_report"), f"Ваш отчет по задаче '{data.get('job')}' отклонили!", reply_markup=bnt_inl)
        conn.commit()
        tempa = [data.get("telegramid_report"), call.from_user.id]
        cur.execute(
            "select job, job_section, photo, job_value, worker_name, telegramid, phone_number, foreman_name, phone_number_foreman, date from `tabWorker report` where status='На рассмотрении' and telegramid=? and telegramidforeman=?",
            tempa)
        a = cur.fetchall()
        cur.execute("select fio from tabEmployer where telegramid=%s" % data.get("telegramid_report"))
        c = cur.fetchall()
        free_work = []
        for i in a:
            st = str(a[0][9])
            free_work.append([InlineKeyboardButton(text=i[0], callback_data=i[5] + "+" + st)])
        free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
        foreman_btn = InlineKeyboardMarkup(
            inline_keyboard=free_work,
        )
        await call.message.edit_text(text="Список отчетов рабочего %s" % c[0][0], reply_markup=foreman_btn)
        await foreman.report_temp_down.set()
    conn.close()

@dp.message_handler(state=foreman.cancel_report)
async def cancel_report(message: Message, state=FSMContext):
    conn = mariadb.connect(
        user=user,
        password=password,
        host=host,
        port=port,
        database=database
    )
    cur = conn.cursor()
    data = await state.get_data()
    mes = message.text
    btn= [[InlineKeyboardButton(text="Понятно", callback_data="Понятно")]]
    bnt_inl = InlineKeyboardMarkup(
        inline_keyboard=btn,
    )
    await bot.send_message(data.get("telegramid_report"), f"Ваш отчет по задаче '{data.get('job')}' отклонили!\nКомментарий: {mes}", reply_markup=bnt_inl)
    conn.commit()
    tempa = [data.get("telegramid_report"), message.from_user.id]
    cur.execute("select job, job_section, photo, job_value, worker_name, telegramid, phone_number, foreman_name, phone_number_foreman, date from `tabWorker report` where status='На рассмотрении' and telegramid=? and telegramidforeman=?",
        tempa)
    a = cur.fetchall()
    cur.execute(f"select fio from tabEmployer where telegramid='{data.get('telegramid_report')}'")
    c = cur.fetchall()
    free_work = []
    for i in a:
        st = str(a[0][9])
        free_work.append([InlineKeyboardButton(text=i[0], callback_data=i[5] + "+" + st)])
    free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
    foreman_btn = InlineKeyboardMarkup(
        inline_keyboard=free_work,
    )
    await message.answer(text="Список отчетов рабочего %s" % c[0][0], reply_markup=foreman_btn)
    await foreman.report_temp_down.set()
    conn.close()
@dp.callback_query_handler(text_contains="serv:Закончить рабочий день", state=foreman.job)
async def end_session(call: CallbackQuery, state=FSMContext):
    now = datetime.datetime.now()
    await call.message.delete()
    await call.message.answer(text="Вы закончили рабочий день", reply_markup=foreman_start_job)
    await state.finish()
