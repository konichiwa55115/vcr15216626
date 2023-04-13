from pyrogram import Client, filters
import subprocess
bot = Client(
    "myfirs",
    api_id=17983098,
    api_hash="ee28199396e0925f1f44d945ac174f64",
    bot_token="6026272284:AAG8qBeaZc5xjYmYfMq1YWsKimoK0D0ap_0"
)
@bot.on_message(filters.command('start') & filters.private)
def command1(bot,message):
    bot.send_message(message.chat.id, "من فضلك اسم المسار الذي تريد الحفظ إليه")
@bot.on_message(filters.private & filters.incoming & filters.text )
    bot.send_message(message.chat.id, "تم حفظ اسم المسار . جار التسجيل ")
    subprocess.call(['python3', 'main.py'])
    subprocess.call(['sudo', 'zip', 'gawr','-r','Gawr])
    subprocess.call(['rclone', 'copy', 'gawr.zip' , 'karim',':',text])
    bot.send_message(message.chat.id, "ستجد التسجيل الخاص بك على المنصة التي حددت  ")

bot.run()
