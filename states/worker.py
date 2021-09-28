from aiogram.dispatcher.filters.state import StatesGroup, State

class worker(StatesGroup):
    job = State()
    no_job = State()
    start_job = State()
    stop_job = State()
    section_task = State()
    task_profile = State()
    input_task = State()
    reg_report = State()
    search = State()
    search_task = State()
    search_input_task = State()
    search_reg_report = State()