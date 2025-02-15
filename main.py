import sqlite3
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes
from config import TELEGRAM_BOT_TOKEN
from database import create_tables, insert_user, fetch_latest_usd_rate, fetch_all_users, insert_currency_rate
from utils import fetch_currency_rates

# مراحل کانورسیشن
INCOME, HOURS, JOB = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! میخوای بدونی واسه چند دلار داری حمالی میکنی بدبخت؟ لطفا درآمد روزانه خود را به تومان وارد کنید:")
    return INCOME

async def get_income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        income = int(update.message.text)
        context.user_data['income'] = income
        await update.message.reply_text("حالا لطفا تعداد ساعات روزانه کار خود را وارد کنید:")
        return HOURS
    except ValueError:
        await update.message.reply_text("لطفا یک عدد صحیح برای درآمد وارد کنید.")
        return INCOME

async def get_hours(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        hours_per_day = int(update.message.text)
        if hours_per_day <= 0 or hours_per_day > 24:
            raise ValueError
        context.user_data['hours_per_day'] = hours_per_day
        await update.message.reply_text("لطفا شغل خود را وارد کنید:")
        return JOB
    except ValueError:
        await update.message.reply_text("لطفا یک عدد صحیح بین 1 تا 24 برای ساعات روزانه کار وارد کنید.")
        return HOURS

async def get_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    job = update.message.text
    context.user_data['job'] = job
    
    # ذخیره اطلاعات کاربر در دیتابیس
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    income = context.user_data['income']
    hours_per_day = context.user_data['hours_per_day']
    job = context.user_data['job']
    
    insert_user(user_id, username, income, hours_per_day, job)
    
    await update.message.reply_text("اطلاعات شما ذخیره شد. منتظر بررسی قیمت ارز هستم...")
    return ConversationHandler.END

async def fetch_currency_rates_job(context: ContextTypes.DEFAULT_TYPE):
    usd_rate, date = fetch_currency_rates()
    insert_currency_rate(date, usd_rate)

async def send_daily_notification(context: ContextTypes.DEFAULT_TYPE):
    users = fetch_all_users()
    latest_rate = fetch_latest_usd_rate()
    
    for user in users:
        user_id, income, hours_per_day = user
        daily_earning_dollar = (income / latest_rate) / hours_per_day
        
        await context.bot.send_message(chat_id=user_id, text=f"حمل پاشو برو برای {daily_earning_dollar:.2f} دلار در روز کار کن.")

def main():
    create_tables()
    
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            INCOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_income)],
            HOURS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_hours)],
            JOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_job)]
        },
        fallbacks=[]
    )
    
    application.add_handler(conv_handler)
    
    # اجرای تابع دریافت قیمت ارز هر 6 ساعت
    job_queue = application.job_queue
    job_queue.run_repeating(fetch_currency_rates_job, interval=6*60*60, first=0)
    
    # ارسال اعلان روزانه
    job_queue.run_daily(send_daily_notification, time=datetime.strptime('23:59', '%H:%M').time())
    
    application.run_polling()

if __name__ == '__main__':
    main()
