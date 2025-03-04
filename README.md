# TaskBot — Telegram-бот для управления задачами

**TaskBot** — это мощный и удобный Telegram-бот, созданный для управления задачами, отслеживания прогресса, мотивации и организации рабочего времени. Бот помогает пользователям создавать задачи, устанавливать приоритеты (высокий, средний, низкий), отмечать задачи как выполненные, удалять их, устанавливать напоминания и брать перерывы по методу Помодоро. Стильный интерфейс с эмодзи и вертикальным меню сделает работу с ботом простой и приятной!

### - Telegram Bot **[@fromex_bot](https://t.me/fromex_bot)**

## ✨ Особенности
- **Создание и управление задачами**: Добавляйте задачи с указанием приоритета (🔴 Высокий, 🟡 Средний, 🟢 Низкий).
- **Отслеживание прогресса**: Показывает процент выполненных задач с визуальной шкалой.
- **Напоминания**: Устанавливайте напоминания на 1 час, 2 часа или задавайте своё время в минутах.
- **Мотивация**: Случайные вдохновляющие сообщения после выполнения задач (например, "Молодец! 🎩").
- **Рабочие перерывы**: Поддержка метода Помодоро (25 минут работы, 5 минут отдыха).
- **Сортировка задач**: Просмотр задач по дате создания.
- **Простой интерфейс**: Вертикальное меню с эмодзи для удобного взаимодействия.

## 🚀 Установка

### Требования
- Python 3.8+
- Telegram Bot API Token от **[@BotFather](https://t.me/BotFather)**
- MongoDB (локально или удалённо)

### Шаги установки
1. **Установите зависимости**
   Убедитесь, что у вас установлен `pip`, и выполните:
   ```bash
   pip install -r requirements.txt
   ```

2. **Настройте конфигурацию**
   Создайте файл `config.py` и укажите ваш токен бота и URI MongoDB:
   ```python
   BOT_TOKEN = "YOUR_BOT_TOKEN_FROM_BOTFATHER"  # Замените на ваш токен
   MONGO_URI = "mongodb://localhost:27017"  # Укажите ваш MongoDB URL
   MONGO_DB = "task_bot_db"
   ```

3. **Запустите бота**
   ```bash
   python main.py
   ```
## 📋 Использование
1. Запустите бота и отправьте команду `/start` в Telegram.
2. Используйте меню с кнопками:
   - **📝 Новые дела**: Введите текст дел и выберите приоритет.
   - **📋 Мои дела**: Посмотрите список дел.
   - **🎲 Случайное дело**: Получите случайную невыполненную задачу.
   - **⏳ Рабочий перерывчик**: Начать 25-минутный рабочий цикл с 5-минутным перерывом.
   - **📈 Как дела?**: Узнайте статистику выполненных и невыполненных задач.
   - **🗑️ Всё выкинуть**: Удалите все задачи.
3. Управляйте задачами с помощью кнопок под каждой задачей: ✅ (закрыть), ✏️ (редактировать), 🗑️ (удалить), ⏰ (напомнить), ⭐ (приоритет).

## 🛠 Структура проекта
```
taskbot/
├── main.py              # Точка входа для запуска бота
├── config.py            # Конфигурационные настройки (токен бота, MongoDB URI)
├── database.py          # Работа с базой данных MongoDB
├── handlers.py          # Обработчики событий и команд бота
├── keyboard.py          # Клавиатуры и кнопки для интерфейса
└── requirements.txt     # Зависимости проекта
```
## 🤝 Контакты
- **Авторы**: **Лесников Евгений Сергеевич, Касаткин Даниил Сергеевич**
- **GitHub**: **[Zxenook](https://github.com/Zxenook)**, **[Danulka3535](https://github.com/Danulka3535)**
- **Telegram**: **[@Zxenook](https://t.me/Zxenook)**, **[@Rengoku_crd](https://t.me/Rengoku_crd)**

Если у вас есть вопросы, предложения или вы нашли баг, пожалуйста, свяжитесь с нами напрямую!

---
