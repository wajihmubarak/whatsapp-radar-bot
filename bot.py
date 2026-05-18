import os
import requests
import telebot
import subprocess
import threading
import time
from telebot import types

# 1. حط توكن بوتك الجبتو من BotFather هنا
BOT_TOKEN = "8735305474:AAF6SwrIEIvglDgfpaamd6ooBXGluLXEzqc"
bot = telebot.TeleBot(BOT_TOKEN)

# 2. الرابط محلي وداخلي 100% جوة Render عبر الـ localhost
BACKEND_URL = "http://127.0.0.1:3000/api"

user_states = {}

# دالة لتشغيل سيرفر الواتساب (index.js) في الخلفية أول ما الحاوية تقوم
def start_node_backend():
    print("🔄 [Render] جاري تشغيل سيرفر الواتساب المساعد في الخلفية...")
    subprocess.Popen(["node", "index.js"])

# تشغيل سيرفر الواتساب في Thread منفصل مع بداية البوت
threading.Thread(target=start_node_backend, daemon=True).start()

# الانتظار ثانيتين للتأكد من قيام السيرفر المساعد بنجاح
time.sleep(2)

@bot.message_handler(commands=['start'])
def main_menu(message):
    markup = types.InlineKeyboardMarkup()
    btn_pair = types.InlineKeyboardButton(text="📱 ربط الواتساب بكود الهاتف", callback_data="start_pairing")
    markup.add(btn_pair)
    
    bot.send_message(
        message.chat.id,
        "🤖 **مرحباً بك في بوت فلترة الواتساب المدمج على Render!**\n\n"
        "اضغط على الزر تحت عشان تربط رقمك وتبدأ الفحص التلقائي بنجاح وبأعلى حماية.",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "start_pairing":
        user_states[call.from_user.id] = "waiting_for_phone"
        bot.send_message(
            call.message.chat.id, 
            "✍️ **الرجاء إرسال رقم الواتساب الخاص بك مع رمز الدولة طوالي:**\n\n"
            "📌 مثال: `249912345678` (اكتب الرقم طوالي بدون علامة + وبدون أصفار في الأول)."
        )

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "waiting_for_phone")
def handle_phone_input(message):
    user_id = message.from_user.id
    phone = "".join(filter(str.isdigit, message.text.strip()))
    user_states[user_id] = None
    
    status_msg = bot.reply_to(message, "🔄 جاري الاتصال بالسيرفر الداخلي وتوليد كود الربط...")
    
    try:
        response = requests.post(f"{BACKEND_URL}/request-code", json={"phone": phone}).json()
        
        if response.get("status") == "success":
            pairing_code = response.get("code")
            bot.delete_message(message.chat.id, status_msg.message_id)
            
            bot.send_message(
                message.chat.id,
                f"🔐 **كود الربط الحقيقي الخاص بك جاهز!**\n\n"
                f"➡️ الكود هو: `{pairing_code}`\n\n"
                f"📋 **خطوات التفعيل في الواتساب:**\n"
                f"1️⃣ افتح تطبيق الواتساب في تلفونك.\n"
                f"2️⃣ اذهب إلى **الأجهزة المرتبطة** -> اضغط **ربط جهاز**.\n"
                f"3️⃣ اختر **الربط باستخدام رقم الهاتف بدلاً من ذلك**.\n"
                f"4️⃣ اكتب الكود الموضح فوق بالترتيب.\n\n"
                f"📥 بعد ما يتم الربط بنجاح، أرسل ملف الأرقام بصيغة (`.txt`) هنا طوالي عشان نفحصها!"
            )
        else:
            bot.edit_message_text("❌ السيرفر الداخلي رفض توليد الكود. تأكد من الرقم وحاول مجدداً.", message.chat.id, status_msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ خطأ في الاتصال بالسيرفر الداخلي الجاري تشغيله...", message.chat.id, status_msg.message_id)

@bot.message_handler(content_types=['document'])
def handle_filter_file(message):
    if not message.document.file_name.endswith('.txt'):
        bot.reply_to(message, "⚠️ رجاءً أرسل ملف نصي ينتهي بـ `.txt` ويحتوي على الأرقام.")
        return

    status_msg = bot.reply_to(message, "⚡ جاري قراءة الملف وبدء الفلترة الفورية من سيرفرات واتساب...")
    
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        numbers = [num.strip() for num in downloaded_file.decode('utf-8').splitlines() if num.strip()]
        
        res = requests.post(f"{BACKEND_URL}/filter", json={"numbers": numbers}).json()
        
        if res.get("status") == "success":
            active_numbers = res.get("active")
            inactive_numbers = res.get("inactive")
            
            output_file = "active_whatsapp.txt"
            with open(output_file, "w") as f:
                f.write("\n".join(active_numbers))
            
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton(text=f"🟢 شغالة: {len(active_numbers)}", callback_data="none"),
                types.InlineKeyboardButton(text=f"🔴 مش شغالة: {len(inactive_numbers)}", callback_data="none")
            )
            
            with open(output_file, "rb") as f:
                bot.send_document(
                    message.chat.id, f, 
                    caption=f"🎯 **اكتملت الفلترة بنجاح!**\n\nالملف المرفق يحتوي على الأرقام الشغالة واتساب وجاهزة للمراسلة.",
                    reply_markup=markup
                )
            os.remove(output_file)
        else:
            bot.reply_to(message, f"❌ خطأ من السيرفر: {res.get('message')}")
            
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ أثناء فحص الملف: تأكد من ربط حسابك أولاً بالضغط على الزر فوق.")
        
    bot.delete_message(message.chat.id, status_msg.message_id)

if __name__ == "__main__":
    bot.infinity_polling()
