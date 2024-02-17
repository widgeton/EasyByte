import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from currencies import Currencies, Loader
from config import settings

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

currencies = Currencies(Loader(settings.CURRENCY_API_TOKEN))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = """
Здравствуйте, {name}!
Этот бот помогает в конвертации валют.
Для этого введите команду: /convert <кол-во> <вал1> to <вал2>
<кол-во> - сумма
<вал1> - валюта суммы
<вала2> - валюта для конвертации
Например: /convert 100 USD to EUR
"""
    user = update.effective_user
    await update.message.reply_text(text.format(name=user.first_name))


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = """
/start - приветствие и описание бота
/help - вывод данного меню описания команд
/currencies - вывод обозначений поддерживаемых валют
/convert <кол-во> <вал1> to <вал2> - конвертация валют
    <кол-во> - сумма
    <вал1> - обозначение валюты суммы
    <вала2> - обозначение валюты для конвертации
    Пример: /convert 100 USD to EUR
"""
    await update.message.reply_text(text)


async def currencies_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    curs = currencies.get_list_currencies()
    await update.message.reply_text('\n'.join(curs))


async def convert(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.message.text
    logger.info(f"Пользователь {update.effective_user} ввел {msg!r}.")
    words = msg.split()

    if len(words) < 5:
        await update.message.reply_text("Команда вызвана неверно. Чтобы посмотреть описание команд введите /help.")
        return

    amount = words[1].strip()
    if not amount.isdecimal():
        text = "Неверно введена сумма. Она должна состоять из цифр и идти после команды convert."
        await update.message.reply_text(text)
        return

    text = "Этот бот не поддерживает валюту с обозначением {cur}. Введите /currencies для просмотра доступных валют."

    from_cur = words[2].strip().upper()
    if not currencies.is_existed(from_cur):
        await update.message.reply_text(text.format(cur=from_cur))
        return

    to_cur = words[4].strip().upper()
    if not currencies.is_existed(to_cur):
        await update.message.reply_text(text.format(cur=to_cur))
        return

    res = currencies.calculate(int(amount), from_cur, to_cur)
    await update.message.reply_text(f"{amount} {from_cur} = {res} {to_cur}")


async def talk(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    greetings = ["привет", "здравствуйте", "доброе утро", "добрый день", "добрый вечер"]
    farewells = ["пока", "до свидания", "до встречи", "прощай"]
    msg = update.message.text.lower()
    name = update.effective_user.first_name

    for grt in greetings:
        if grt in msg:
            await update.message.reply_text(f"Здравствуйте, {name}!")
            return

    for frw in farewells:
        if frw in msg:
            await update.message.reply_text(f"До свидания, {name}! Было приятно с вами поработать.")
            return


def main() -> None:
    application = Application.builder().token(settings.BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("convert", convert))
    application.add_handler(CommandHandler("currencies", currencies_command))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, talk))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
