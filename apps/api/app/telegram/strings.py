"""Localized bot copy for the four supported learner languages.

Uzbek is formal (``siz``) by default and praises effort, per the product rules.
Use :func:`t` to look up a key with graceful fallback to Uzbek Latin.
"""

from typing import Any

DEFAULT_LANG = "uz-latn"

STRINGS: dict[str, dict[str, str]] = {
    "uz-latn": {
        "greet": (
            "Assalomu alaykum! Men Ilm AI yordamchingizman. 📚\n\n"
            "Hisobingizni ulash uchun web-ilovadan kodni oling va /link KOD deb yuboring.\n"
            "Buyruqlar uchun /help."
        ),
        "greet_linked": "Assalomu alaykum! Xush kelibsiz. 📚 Buyruqlar: /help",
        "linked": "✅ {email} hisobiga ulandingiz!",
        "link_invalid": "❌ Kod noto'g'ri yoki allaqachon ishlatilgan. Web-ilovadan yangi kod oling.",
        "link_usage": "Foydalanish: /link KOD\nKodni web-ilovadagi Telegram sahifasidan oling.",
        "help": (
            "Buyruqlar:\n"
            "/link KOD — hisobni ulash\n"
            "/today — bugungi reja\n"
            "/quiz — tezkor test\n"
            "/streak — ketma-ket kunlar\n"
            "/lang uz|ru|en — tilni o'zgartirish\n"
            "/help — yordam"
        ),
        "lang_set": "✅ Til o'zgartirildi.",
        "lang_usage": "Foydalanish: /lang uz | uzc | ru | en",
        "lang_not_linked": "Avval hisobni ulang: /link KOD",
        "need_link": "Avval hisobni ulang: /link KOD",
        "today_header": "📅 Bugungi reja:",
        "today_empty": "Bugun uchun reja yo'q. Web-ilovada reja tuzing.",
        "today_btn": "Rejani ochish",
        "streak": "🔥 {n} kun ketma-ket! Ajoyib harakat, shu zaylda davom eting.",
        "streak_zero": "Hali ketma-ketlik yo'q. Bugun bitta test ishlang! 💪",
        "quiz_no_material": "Avval web-ilovada material yuklang, keyin test ishlay olasiz.",
        "quiz_intro": "📝 Tezkor test. Variantlardan birini tanlang:",
        "quiz_correct": "✅ To'g'ri!\n\n{rationale}",
        "quiz_wrong": "❌ Noto'g'ri. To'g'ri javob: {correct}\n\n{rationale}",
        "quiz_done": "🎉 Test tugadi! Natija: {correct}/{total}. Harakatingiz uchun rahmat!",
        "daily_push": "Salom! Bugungi rejangiz tayyor. 📅",
        "error": "Kechirasiz, xatolik yuz berdi. Birozdan so'ng qayta urinib ko'ring.",
    },
    "uz-cyrl": {
        "greet": (
            "Ассалому алайкум! Мен Илм AI ёрдамчингизман. 📚\n\n"
            "Ҳисобингизни улаш учун web-иловадан кодни олинг ва /link КОД деб юборинг.\n"
            "Буйруқлар учун /help."
        ),
        "greet_linked": "Ассалому алайкум! Хуш келибсиз. 📚 Буйруқлар: /help",
        "linked": "✅ {email} ҳисобига уландингиз!",
        "link_invalid": "❌ Код нотўғри ёки аллақачон ишлатилган. Web-иловадан янги код олинг.",
        "link_usage": "Фойдаланиш: /link КОД\nКодни web-иловадаги Telegram саҳифасидан олинг.",
        "help": (
            "Буйруқлар:\n"
            "/link КОД — ҳисобни улаш\n"
            "/today — бугунги режа\n"
            "/quiz — тезкор тест\n"
            "/streak — кетма-кет кунлар\n"
            "/lang uz|ru|en — тилни ўзгартириш\n"
            "/help — ёрдам"
        ),
        "lang_set": "✅ Тил ўзгартирилди.",
        "lang_usage": "Фойдаланиш: /lang uz | uzc | ru | en",
        "lang_not_linked": "Аввал ҳисобни уланг: /link КОД",
        "need_link": "Аввал ҳисобни уланг: /link КОД",
        "today_header": "📅 Бугунги режа:",
        "today_empty": "Бугун учун режа йўқ. Web-иловада режа тузинг.",
        "today_btn": "Режани очиш",
        "streak": "🔥 {n} кун кетма-кет! Ажойиб ҳаракат, шу зайлда давом этинг.",
        "streak_zero": "Ҳали кетма-кетлик йўқ. Бугун битта тест ишланг! 💪",
        "quiz_no_material": "Аввал web-иловада материал юкланг, кейин тест ишлай оласиз.",
        "quiz_intro": "📝 Тезкор тест. Вариантлардан бирини танланг:",
        "quiz_correct": "✅ Тўғри!\n\n{rationale}",
        "quiz_wrong": "❌ Нотўғри. Тўғри жавоб: {correct}\n\n{rationale}",
        "quiz_done": "🎉 Тест тугади! Натижа: {correct}/{total}. Ҳаракатингиз учун раҳмат!",
        "daily_push": "Салом! Бугунги режангиз тайёр. 📅",
        "error": "Кечирасиз, хатолик юз берди. Бироздан сўнг қайта уриниб кўринг.",
    },
    "ru": {
        "greet": (
            "Здравствуйте! Я ваш помощник Ilm AI. 📚\n\n"
            "Чтобы привязать аккаунт, получите код в веб-приложении и отправьте /link КОД.\n"
            "Команды: /help."
        ),
        "greet_linked": "Здравствуйте! С возвращением. 📚 Команды: /help",
        "linked": "✅ Вы привязали аккаунт {email}!",
        "link_invalid": "❌ Код неверный или уже использован. Получите новый в веб-приложении.",
        "link_usage": "Использование: /link КОД\nКод можно получить на странице Telegram в веб-приложении.",
        "help": (
            "Команды:\n"
            "/link КОД — привязать аккаунт\n"
            "/today — план на сегодня\n"
            "/quiz — быстрый тест\n"
            "/streak — дни подряд\n"
            "/lang uz|ru|en — сменить язык\n"
            "/help — помощь"
        ),
        "lang_set": "✅ Язык изменён.",
        "lang_usage": "Использование: /lang uz | uzc | ru | en",
        "lang_not_linked": "Сначала привяжите аккаунт: /link КОД",
        "need_link": "Сначала привяжите аккаунт: /link КОД",
        "today_header": "📅 План на сегодня:",
        "today_empty": "На сегодня плана нет. Создайте план в веб-приложении.",
        "today_btn": "Открыть план",
        "streak": "🔥 {n} дней подряд! Отличная работа, продолжайте в том же духе.",
        "streak_zero": "Серии пока нет. Пройдите тест сегодня! 💪",
        "quiz_no_material": "Сначала загрузите материал в веб-приложении, затем сможете пройти тест.",
        "quiz_intro": "📝 Быстрый тест. Выберите один из вариантов:",
        "quiz_correct": "✅ Верно!\n\n{rationale}",
        "quiz_wrong": "❌ Неверно. Правильный ответ: {correct}\n\n{rationale}",
        "quiz_done": "🎉 Тест завершён! Результат: {correct}/{total}. Спасибо за старание!",
        "daily_push": "Привет! Ваш план на сегодня готов. 📅",
        "error": "Извините, произошла ошибка. Попробуйте позже.",
    },
    "en": {
        "greet": (
            "Hello! I'm your Ilm AI study companion. 📚\n\n"
            "To link your account, get a code in the web app and send /link CODE.\n"
            "See /help for commands."
        ),
        "greet_linked": "Hello! Welcome back. 📚 Commands: /help",
        "linked": "✅ Connected to {email}!",
        "link_invalid": "❌ That code is invalid or already used. Get a new one in the web app.",
        "link_usage": "Usage: /link CODE\nGet the code on the Telegram page in the web app.",
        "help": (
            "Commands:\n"
            "/link CODE — connect your account\n"
            "/today — today's plan\n"
            "/quiz — quick quiz\n"
            "/streak — day streak\n"
            "/lang uz|ru|en — change language\n"
            "/help — help"
        ),
        "lang_set": "✅ Language updated.",
        "lang_usage": "Usage: /lang uz | uzc | ru | en",
        "lang_not_linked": "Link your account first: /link CODE",
        "need_link": "Link your account first: /link CODE",
        "today_header": "📅 Today's plan:",
        "today_empty": "No plan for today. Create one in the web app.",
        "today_btn": "Open plan",
        "streak": "🔥 {n}-day streak! Great effort — keep it up.",
        "streak_zero": "No streak yet. Do a quiz today! 💪",
        "quiz_no_material": "Upload a material in the web app first, then you can take a quiz.",
        "quiz_intro": "📝 Quick quiz. Pick one option:",
        "quiz_correct": "✅ Correct!\n\n{rationale}",
        "quiz_wrong": "❌ Incorrect. Correct answer: {correct}\n\n{rationale}",
        "quiz_done": "🎉 Quiz done! Score: {correct}/{total}. Thanks for the effort!",
        "daily_push": "Hi! Your plan for today is ready. 📅",
        "error": "Sorry, something went wrong. Please try again later.",
    },
}


def t(lang: str, key: str, **kwargs: Any) -> str:
    table = STRINGS.get(lang) or STRINGS[DEFAULT_LANG]
    template = table.get(key) or STRINGS[DEFAULT_LANG].get(key, key)
    return template.format(**kwargs) if kwargs else template
