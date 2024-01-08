from aiogram.fsm.state import StatesGroup, State


class Authorise(StatesGroup):
    fullname = State()


class FSMStartShift(StatesGroup):
    place = State()
    policy = State()
    my_photo = State()
    my_video = State()
    wait_for_defects = State()
    photo_of_defects = State()
    wheels = State()
    train_flash = State()
    train_clean = State()
    recorder = State()
    thomas = State()


class FSMEncashment(StatesGroup):
    place = State()
    photo_of_check = State()
    summary = State()
    date_of_cash = State()
    null_encashment = State()


class FSMAttractionsCheck(StatesGroup):
    place = State()
    bill_acceptor = State()
    defects_on_bill_acceptor = State()
    attracts = State()
    defects_on_attracts = State()


class FSMFinishShift(StatesGroup):
    place = State()
    count_of_visitors = State()
    beneficiaries = State()
    photo_of_beneficiaries = State()
    summary = State()
    cash = State()
    online_cash = State()
    qr_code = State()
    expenditure = State()
    salary = State()
    encashment = State()
    necessary_photos = State()
    charge = State()
    charge_video = State()


class FSMAdmin(StatesGroup):
    stats = State()
    money = State()
    money_by_hand = State()
    visitors = State()
    visitors_by_hand = State()
