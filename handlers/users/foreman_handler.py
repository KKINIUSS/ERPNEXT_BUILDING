from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from loader import dp
from aiogram.dispatcher import FSMContext
from keyboards.default.foreman_job import foreman_start_job
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


@dp.callback_query_handler(text_contains="serv:Журнал учёта специалистов", state=foreman.job)
async def check_time(call: CallbackQuery, state=FSMContext):
    conn = mariadb.connect(
        user=user,
        password=password,
        host=host,
        port=port,
        database=database
    )
    cur = conn.cursor()
    cur.execute("select fio, telegramid, name from `tabWorker activity temp` where telegramidforeman=%s" %call.from_user.id)
    a = cur.fetchall()
    free_work = []
    for i in a:
        free_work.append([InlineKeyboardButton(text=i[0], callback_data=i[2])])
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
        cur.execute(f"select fio, time_join, telegramidforeman, name, date, telegramid from `tabWorker activity temp` where name='{str}'")
        a = cur.fetchall()
        cur.execute("select phone_number from tabEmployer where telegramid=%s" % str)
        tg = cur.fetchall()
        free_work = [[InlineKeyboardButton(text="Принять", callback_data="Принять")], [InlineKeyboardButton(text="Отклонить", callback_data="Отклонить")], [InlineKeyboardButton(text="Назад", callback_data="Назад")]]
        time_work = ""
        time_work = a[0][1]
        foreman_choise_free_btn = InlineKeyboardMarkup(
            inline_keyboard=free_work,
        )
        await call.message.edit_text(f"Имя специалиста {a[0][0]}\nНомер телефона: {tg[0][0]}\n"
                                     f"Дата: {a[0][4]}\nВремя прихода на работу: {time_work}", reply_markup=foreman_choise_free_btn)
        await state.update_data(telegramid=a[0][5], fio=a[0][0], time_join=a[0][1], date=a[0][4], telegramidforeman=a[0][2], date_worker=str)
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
        cur.execute("select fio, telegramid, name from `tabWorker activity temp` where telegramidforeman=%s" % call.from_user.id)
        a = cur.fetchall()
        free_work = []
        for i in a:
            free_work.append([InlineKeyboardButton(text=i[0], callback_data=i[2])])
        free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
        foreman_btn = InlineKeyboardMarkup(
            inline_keyboard=free_work,
        )
        await call.message.edit_text(text="Список отметившихся", reply_markup=foreman_btn)
        await foreman.activity_worker.set()
    elif(stri == "Принять"):
        data = await state.get_data()
        mas = [data.get("date_worker"), datetime.datetime.now(), "Administrator", data.get("fio"), data.get("time_join"), '', data.get("telegramid"), data.get("telegramidforeman"), data.get("date")]
        cur.execute("insert into `tabWorker activity` (name ,creation ,owner, fio, time_join, date_end, telegramid, telegramidforeman, date)"
            " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", mas)
        cur.execute(f"delete from `tabWorker activity temp` where name='{data.get('date_worker')}'")
        conn.commit()
        cur.execute("select fio, telegramid, name from `tabWorker activity temp` where telegramidforeman=%s" % call.from_user.id)
        a = cur.fetchall()
        free_work = []
        await call.message.delete()
        await call.message.answer("Принято!")
        for i in a:
            free_work.append([InlineKeyboardButton(text=i[0], callback_data=i[2])])
        free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
        foreman_btn = InlineKeyboardMarkup(
            inline_keyboard=free_work,
        )
        await call.message.answer(text="Список отметившихся", reply_markup=foreman_btn)
        await foreman.activity_worker.set()
    elif(stri == "Отклонить"):
        data = await state.get_data()
        j = data.get("telegramid")
        j = int(j)
        btn = []
        btn.append([InlineKeyboardButton(text="Понятно", callback_data="Понятно")])
        bnt_inl = InlineKeyboardMarkup(
            inline_keyboard=btn,
        )
        await bot.send_message(j, "Сообщение от прораба: "
                                  "Ваш данные начала работы отклонены!", reply_markup=bnt_inl)
        cur.execute(f"delete from `tabWorker activity temp` where name='{data.get('date_worker')}'")
        conn.commit()
        await call.message.delete()
        await call.message.answer("Отклонено!")
        cur.execute("select fio, telegramid, name from `tabWorker activity temp` where telegramidforeman=%s" % call.from_user.id)
        a = cur.fetchall()
        free_work = []
        for i in a:
            free_work.append([InlineKeyboardButton(text=i[0], callback_data=i[2])])
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
        cur.execute(f"select fio, phone_number, telegramid, comments_foreman, photo, photo_pass from tabEmployer where status='Подтвержден' and telegramid='{str}'")
        a = cur.fetchall()
        free_work = []
        free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
        foreman_choise_free_btn = InlineKeyboardMarkup(
            inline_keyboard=free_work,
        )
        await call.message.edit_text(f"Профиль специалиста {a[0][0]}\nНомер телефона: {a[0][1]}\nКомментарий предыдущего прораба: {a[0][3]}\n", reply_markup=foreman_choise_free_btn)
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
        cur.execute(f"select fio, telegramid from tabEmployer where status='Подтвержден' and telegramidforeman='{call.from_user.id}'")
        a = cur.fetchall()
        free_work = []
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
    cur.execute(f"select distinct worker_name, telegramid"
                f" from `tabWorker report` where status='На рассмотрении' and telegramidforeman='{call.from_user.id}'")
    a = cur.fetchall()
    free_work = []
    for i in a:
        free_work.append([InlineKeyboardButton(text=i[0] , callback_data=i[1])])
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
        cur.execute("select job, job_section, photo, job_value, worker_name, telegramid, phone_number, foreman_name, phone_number_foreman, date, time"
                " from `tabWorker report` where status='На рассмотрении' and telegramidforeman=? and telegramid=?", mas_data)
        a = cur.fetchall()
        mis = [stri]
        cur.execute("select fio from tabEmployer where telegramid=?", mis)
        c = cur.fetchall()
        free_work = []
        for i in a:
            st = str(i[9]) + "+" + str(i[10])
            free_work.append([InlineKeyboardButton(text=i[0] , callback_data=i[5] + "+" + st)])
        free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
        foreman_btn = InlineKeyboardMarkup(
            inline_keyboard=free_work,
        )
        await call.message.edit_text(text=f"Список отчетов специалиста {c[0][0]}", reply_markup=foreman_btn)
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
        cur.execute(f"select distinct worker_name, telegramid"
            f" from `tabWorker report` where status='На рассмотрении' and telegramidforeman='{call.from_user.id}'")
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
                    "foreman_name, telegramidforeman, phone_number_foreman, date, task_name, name, time "
                    "from `tabWorker report` where status='На рассмотрении' and telegramid=? and date=? and time=?", mas)
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
        await call.message.edit_text(f"Название работы: {a[0][0]}\nРаздел работы: {a[0][1]}\nОбъем работ: {a[0][3]}\nВыполнено на текущих момент: {b[0][1]}\n"
                                     f"Общий объем работ: {b[0][0]}\nНомер телефона специалиста: {a[0][6]}\nИмя специалиста: {a[0][4]}\nДата отчета: {a[0][10] + ' ' + a[0][13]}", reply_markup=foreman_choise_free_btn)
        await state.update_data(job=a[0][0], job_section=a[0][1], telegramid_report=a[0][5],
                                photo_work=a[0][2], job_value=a[0][3],
                                worker_name=a[0][4], phone_number_worker_report=a[0][6],
                                foreman_report_name=a[0][7], telegramid_report_forename=a[0][8],
                                foreman_report_phone_number=a[0][9], date=a[0][10], task_name=a[0][11], report_name=a[0][12])
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
        await call.message.edit_text(text="Список отчетов специалиста %s" %c[0][0], reply_markup=foreman_btn)
        await foreman.report_temp_down.set()
    elif(stri == "Принять"):
        data = await state.get_data()
        await state.update_data(telegramid_report=data.get("telegramid_report"))
        temp=[]
        temp.append(data.get("telegramid_report"))
        temp.append(data.get("date"))
        cur.execute(f"select job, job_section, photo, job_value, worker_name, telegramid, phone_number, foreman_name, telegramidforeman,"
                    f"phone_number_foreman, date, task_name, name from `tabWorker report` where name='{data.get('report_name')}'")
        a = cur.fetchall()
        cur.execute(f"update `tabWorker report` set status='Принято' where name='{data.get('report_name')}'")
        conn.commit()
        cur.execute(f"select amount, progress_amount from tabTask where name='{a[0][11]}'")
        b = cur.fetchall()
        job_value = a[0][3]
        job_max = b[0][0]
        job_current_value = b[0][1]
        if(job_max != 0):
            progress = (float(job_value) / float(job_max)) * 100
        else:
            progress = 0
        progress_amount = float(job_current_value) + float(job_value)
        mes = [progress_amount, float(progress), a[0][11]]
        cur.execute("update tabTask set progress_amount=?, progress=? where name=?", mes)
        await call.message.delete()
        await call.message.answer("Прогресс по задаче обновлён. Отчет занесён в базу!")
        conn.commit()
        tempa = [temp[0], call.from_user.id]
        cur.execute("select job, job_section, photo, job_value, worker_name, telegramid, "
                    "phone_number, foreman_name, phone_number_foreman, date, time from "
                    "`tabWorker report` where status='На рассмотрении' and telegramid=? and telegramidforeman=?", tempa)
        a = cur.fetchall()
        cur.execute(f"select fio from tabEmployer where telegramid='{temp[0]}'")
        c = cur.fetchall()
        free_work = []
        for i in a:
            free_work.append([InlineKeyboardButton(text=i[0], callback_data=i[5] + "+" + str(a[0][9]) + "+" + str(a[0][10]))])
        free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
        foreman_btn = InlineKeyboardMarkup(
            inline_keyboard=free_work,
        )
        await call.message.answer(text="Список отчетов специалиста %s" % c[0][0], reply_markup=foreman_btn)
        await foreman.report_temp_down.set()
    elif (stri == "Отклонить"):
        data = await state.get_data()
        await state.update_data(telegramid_report=data.get("telegramid_report"))
        temp = [data.get("telegramid_report"), data.get("date")]
        cur.execute(f"update `tabWorker report` set status='Отклонен' where name='{data.get('report_name')}'")
        conn.commit()
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
        cur.execute("select job, job_section, photo, job_value, worker_name, telegramid, phone_number, foreman_name, "
                    "phone_number_foreman, date, time from `tabWorker report` where status='На рассмотрении' and telegramid=? and telegramidforeman=?",
            tempa)
        a = cur.fetchall()
        cur.execute("select fio from tabEmployer where telegramid=%s" % data.get("telegramid_report"))
        c = cur.fetchall()
        free_work = []
        for i in a:
            st = str(a[0][9]) + "+" + str(a[0][10])
            free_work.append([InlineKeyboardButton(text=i[0], callback_data=i[5] + "+" + st)])
        free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
        foreman_btn = InlineKeyboardMarkup(
            inline_keyboard=free_work,
        )
        await call.message.edit_text(text="Список отчетов специалиста %s" % c[0][0], reply_markup=foreman_btn)
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
    conn.commit()
    data = await state.get_data()
    mes = message.text
    btn= [[InlineKeyboardButton(text="Понятно", callback_data="Понятно")]]
    bnt_inl = InlineKeyboardMarkup(
        inline_keyboard=btn,
    )
    await bot.send_message(data.get("telegramid_report"), f"Ваш отчет по задаче '{data.get('job')}' отклонили!\nКомментарий: {mes}", reply_markup=bnt_inl)
    conn.commit()
    tempa = [data.get("telegramid_report"), message.from_user.id]
    cur.execute("select job, job_section, photo, job_value, worker_name, telegramid, phone_number, "
                "foreman_name, phone_number_foreman, date, time from `tabWorker report` where status='На рассмотрении' and telegramid=? and telegramidforeman=?",
        tempa)
    a = cur.fetchall()
    cur.execute(f"select fio from tabEmployer where telegramid='{data.get('telegramid_report')}'")
    c = cur.fetchall()
    free_work = []
    for i in a:
        st = str(a[0][9]) + "+" + str(a[0][10])
        free_work.append([InlineKeyboardButton(text=i[0], callback_data=i[5] + "+" + st)])
    free_work.append([InlineKeyboardButton(text="Назад", callback_data="Назад")])
    foreman_btn = InlineKeyboardMarkup(
        inline_keyboard=free_work,
    )
    await message.answer(text="Список отчетов специалиста %s" % c[0][0], reply_markup=foreman_btn)
    await foreman.report_temp_down.set()
    conn.close()
@dp.callback_query_handler(text_contains="serv:Закончить рабочий день", state=foreman.job)
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
    data = await state.get_data()
    cur.execute(f"update `tabWorker activity` set time_end='{datetime.now().strftime('%H:%M:%S')}' where name='{data.get('date_foreman')}'")
    await call.message.delete()
    await call.message.answer(text="Вы закончили рабочий день", reply_markup=foreman_start_job)
    await state.finish()
    conn.close()
