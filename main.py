import sqlite3
from datetime import datetime, timedelta
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
from config import TELEGRAM_BOT_TOKEN
from database import create_tables, insert_user, fetch_latest_usd_rate, fetch_all_users, insert_currency_rate
from utils import fetch_currency_rates

# مراحل کانورسیشن
INCOME, HOURS, JOB = range(3)

def start(update, context):
    update.message.reply_text("سلام! میخوای بدونی واسه چند دلار داری حمالی میکنی بدبخت؟ حال درآمد روزانه خود را به تومان وارد کنید:")
    return INCOME

def get_income(update, context):
    try:
        income = int(update.message.text)
        context.user_data['income'] = income
        update.message.reply_text("حالا لطفا تعداد ساعات روزانه کار خود را وارد کنید:")
        return HOURS
    except ValueError:
        update.message.reply_text("لطفا یک عدد صحیح برای درآمد وارد کنید.")
        return INCOME

def get_hours(update, context):
    try:
        hours_per_day = int(update.message.text)
        if hours_per_day <= 0 or hours_per_day > 24:
            raise ValueError
        context.user_data['hours_per_day'] = hours_per_day
        update.message.reply_text("لطفا شغل خود را وارد کنید:")
        return JOB
    except ValueError:
        update.message.reply_text("لطفا یک عدد صحیح بین 1 تا 24 برای ساعات روزانه کار وارد کنید.")
        return HOURS

def get_job(update, context):
    job = update.message.text
    context.user_data['job'] = job
    
    # ذخیره اطلاعات کاربر در دیتابیس
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    income = context.user_data['income']
    hours_per_day = context.user_data['hours_per_day']
    job = context.user_data['job']
    
    insert_user(user_id, username, income, hours_per_day, job)
    
    update.message.reply_text("اطلاعات شما ذخیره شد. منتظر بررسی قیمت ارز هستم...")
    return ConversationHandler.END

def fetch_currency_rates_job(context):
    usd_rate, date = fetch_currency_rates()
    insert_currency_rate(date, usd_rate)

def send_daily_notification(context):
    users = fetch_all_users()
    latest_rate = fetch_latest_usd_rate()
    
    for user in users:
        user_id, income, hours_per_day = user
        daily_earning_dollar = (income / latest_rate) / hours_per_day
        
        context.bot.send_message(chat_id=user_id, text=f"حمل پاشو برو برای {daily_earning_dollar:.2f} دلار در روز کار کن.")

def main():
    create_tables()
    
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            INCOME: [MessageHandler(Filters.text & ~Filters.command, get_income)],
            HOURS: [MessageHandler(Filters.text & ~Filters.command, get_hours)],
            JOB: [MessageHandler(Filters.text & ~Filters.command, get_job)]
        },
        fallbacks=[]
    )
    
    dp.add_handler(conv_handler)
    
    # اجرای تابع دریافت قیمت ارز هر 6 ساعت
    job_queue = updater.job_queue
    job_queue.run_repeating(fetch_currency_rates_job, interval=6*60*60, first=0)
    
    # ارسال اعلان روزانه
    job_queue.run_daily(send_daily_notification, time=datetime.strptime('23:59', '%H:%M').time())
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()