# Домашнее задание по теме "Инлайн клавиатуры".
# Цель: научится создавать Inline клавиатуры и кнопки на них в Telegram-bot.

# # Установлен Aiogram последней версии для Python 3.12!!!

from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton  # для выбора пола человека сделаем кнопки
import asyncio

# Инициализация бота и диспетчера
TOKEN = "My_Token"
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)

# Создание инлайн-клавиатуры с двумя кнопками
button_calories = InlineKeyboardButton(text='Рассчитать норму калорий', callback_data='calories')
button_formulas = InlineKeyboardButton(text='Формулы расчёта', callback_data='formulas')
inline_kb = InlineKeyboardMarkup(inline_keyboard=[[button_calories], [button_formulas]]) # кнопки располагаю
# друг над другом потому что не виден полностью текст кнопки если расположить одной строкой


# Определение состояний пользователя
class UserState(StatesGroup): # создаем класс, который наследуется от группы состояний
    gender = State()  # Добавим еще пол человека
    age = State() # экземпляр класса State для определения состояния возраста
    growth = State() # ...состояния роста
    weight = State() # ...состояния веса


# Создание клавиатуры для выбора пола
def gender_keyboard():
    buttons_sex = [KeyboardButton(text="Мужчина"), KeyboardButton(text="Женщина")]
    return ReplyKeyboardMarkup(keyboard=[buttons_sex], resize_keyboard=True, one_time_keyboard=True) # Когда
    # one_time_keyboard=True, клавиатура автоматически скрывается после первого нажатия на любую кнопку


# Проверка, является ли вводимое значение положительным целым числом
# value.isdigit() — проверяем, что строка состоит только из цифр.
# int(value) > 0 — проверяем, что число положительное.
def is_valid_number(value):
    return value.isdigit() and int(value) > 0


# Команда start
@dp.message(Command("start")) # Декоратор, который связывает хендлер с командой /start
async def start_form(message: Message): # Отправляет приветственное сообщение и инлайн-клавиатуру с кнопкой "Рассчитать"
    await message.answer("Привет! Я бот, помогающий твоему здоровью. Если хочешь узнать свою суточную норму "
                         "калорий, то нажми 'Рассчитать'.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Рассчитать', callback_data='main_menu')]]))


# Функция для отображения основного меню
@router.callback_query(F.data == 'main_menu')
async def main_menu(call: CallbackQuery): # функция отвечает за отправку сообщения с текстом  "Выберите опцию:"
    # и инлайн-клавиатурой, созданной ранее (inline_kb), у нее 2 кнопки: "Рассч норму калорий" и "Формулы расчёта"
    await call.message.answer("Выберите опцию:", reply_markup=inline_kb)


# Функция для отображения формул расчёта
@router.callback_query(F.data == 'formulas')
async def get_formulas(call: CallbackQuery):
    formula_text = ("Формула Миффлина-Сан Жеора:\n"
                    "Для мужчин: 10 * вес (кг) + 6.25 * рост (см) - 5 * возраст (лет) + 5\n"
                    "Для женщин: 10 * вес (кг) + 6.25 * рост (см) - 5 * возраст (лет) - 161")
    await call.message.answer(formula_text)


# Функция для начала процесса расчета калорий
@router.callback_query(F.data == 'calories') # Когда  нажимаем кнопку с callback_data='calories', бот отправляет
# сообщение с клавиатурой для выбора пола
async def set_gender(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Выберите ваш пол:", reply_markup=gender_keyboard())
    await state.set_state(UserState.gender)


# Хендлер для обработки выбора пола
@router.message(UserState.gender)
async def set_age(message: types.Message, state: FSMContext):
    gender = message.text.lower() # приводим к нижнему регистру текст кнопок выбора пола
    if gender not in ["мужчина", "женщина"]:
        await message.answer("Пожалуйста, выберите пол, используя кнопки ниже.")
        return
    await state.update_data(gender=gender) # обновляем данные состояния, сохраняя пол пользователя
    await message.answer("Введите свой возраст:", reply_markup=types.ReplyKeyboardRemove()) # бот отправляет
    # сообщение с просьбой ввести возраст и ReplyKeyboardRemove: Убирает клавиатуру после выбора пола
    await state.set_state(UserState.age) # устанавливаем состояние age, где бот ожидает ввода возраста


# Хендлер для обработки возраста
@router.message(UserState.age)
async def set_growth(message: types.Message, state: FSMContext):
    if is_valid_number(message.text):
        await state.update_data(age=int(message.text))  # обновляет данные состояния, сохраняя возраст пользователя
        await message.answer("Введите свой рост (в см):")
        await state.set_state(UserState.growth)  # устанавливаем состояние growth, где бот ожидает ввода роста
    else:
        await message.answer("Возраст должен быть положительным числом. Пожалуйста, введите корректное значение.")


# Хендлер для обработки роста
@router.message(UserState.growth)
async def set_weight(message: types.Message, state: FSMContext):
    if is_valid_number(message.text):
        await state.update_data(growth=int(message.text)) # обновляет данные состояния, сохраняя рост пользователя
        await message.answer("Введите свой вес (в кг):")
        await state.set_state(UserState.weight)  # устанавливаем состояние weight, где бот ожидает ввода веса
    else:
        await message.answer("Рост должен быть положительным числом. Пожалуйста, введите корректное значение.")


# Хендлер для обработки веса и вычисления нормы калорий
@router.message(UserState.weight)
async def send_calories(message: types.Message, state: FSMContext):
    if is_valid_number(message.text):
        await state.update_data(weight=int(message.text)) # обновляет данные состояния, сохраняя вес пользователя
        data = await state.get_data() # извлекаем все данные введенные пользователем (пол, возраст, рост, вес)

        gender = data['gender']
        age = data['age']
        growth = data['growth']
        weight = data['weight']

        # Формула Миффлина - Сан Жеора для мужчин и женщин
        if gender == "мужчина":
            calories = 10 * weight + 6.25 * growth - 5 * age + 5
        else:
            calories = 10 * weight + 6.25 * growth - 5 * age - 161

        await message.answer(f"Ваша норма калорий: {calories:.2f} ккал в день.")

        await state.clear()  # Завершение машины состояний
    else:
        await message.answer("Вес должен быть положительным числом. Пожалуйста, введите корректное значение.")


# Хендлер для перенаправления всех остальных сообщений на start
@router.message(~F.text.lower('Рассчитать') and ~F.state(UserState.age) and ~F.state(UserState.growth)
                and ~F.state(UserState.weight))
async def redirect_to_start(message: types.Message):
    await start_form(message)  # Перенаправляем сообщение на хендлер команды /start


# Основная функция запуска бота
async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
