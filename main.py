import telebot
from telebot import types
import os
import json
from keep_alive import keep_alive

# ==== CONFIG ====
BOT_TOKEN = '7329361068:AAE7-6u7RC0jqouIvLAdpaV6xtjXWJEcN-w'
GROUP_ID = -1002534069646  # Your group ID
GROUP_LINK = "https://t.me/TTNCoin"
bot = telebot.TeleBot(BOT_TOKEN)

# ==== LOAD DATA ====
if os.path.exists("user_data.json"):
    with open("user_data.json", "r") as f:
        data = json.load(f)
else:
    data = {}

# ==== SAVE DATA ====
def save_data():
    with open("user_data.json", "w") as f:
        json.dump(data, f, indent=4)

# ==== START COMMAND ====
@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    user_name = message.from_user.first_name
    username = message.from_user.username or ""

    if user_id not in data:
        data[user_id] = {
            "name": user_name,
            "username": f"@{username}" if username else "N/A",
            "referrals": 0,
            "joined": False,
            "wallet": "",
            "referred_by": ""
        }

    else:
        data[user_id]["name"] = user_name
        data[user_id]["username"] = f"@{username}" if username else "N/A"

    # Handle referral
    args = message.text.split()
    if len(args) > 1:
        referrer = args[1]
        if referrer != user_id:
            if referrer not in data:
                data[referrer] = {
                    "name": "",
                    "username": "",
                    "referrals": 0,
                    "joined": False,
                    "wallet": "",
                    "referred_by": ""
                }
            if data[user_id].get("referred_by") != referrer:
                data[referrer]["referrals"] += 1
                data[user_id]["referred_by"] = referrer

    # Group check
    try:
        member = bot.get_chat_member(GROUP_ID, message.from_user.id)
        data[user_id]["joined"] = member.status in ['member', 'creator', 'administrator']
    except:
        data[user_id]["joined"] = False

    save_data()

    referral_link = f"https://t.me/{bot.get_me().username}?start={user_id}"
    count = data[user_id]["referrals"]
    joined = "✅" if data[user_id]["joined"] else "❌"
    wallet = "✅" if data[user_id]["wallet"] else "❌"

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📣 Share Referral", switch_inline_query=referral_link))
    markup.add(types.InlineKeyboardButton("👥 Join Group", url=GROUP_LINK))
    markup.add(types.InlineKeyboardButton("🔗 Connect Wallet", callback_data="connect_wallet"))

    bot.send_message(message.chat.id,
                     f"👋 Welcome {user_name}!\n\n"
                     f"💰 Your referral link:\n{referral_link}\n\n"
                     f"👥 Referred: {count}/5\n"
                     f"📢 Group Joined: {joined}\n"
                     f"🔗 Wallet: {wallet}",
                     reply_markup=markup)

# ==== CALLBACK FOR CONNECT WALLET ====
@bot.callback_query_handler(func=lambda call: call.data == "connect_wallet")
def ask_wallet(call):
    bot.send_message(call.message.chat.id, "🔐 Send your Phantom wallet address:")
    bot.register_next_step_handler(call.message, save_wallet)

def is_valid_wallet(address):
    # Simple wallet check (Solana: 32-44 chars base58)
    return len(address) >= 32 and len(address) <= 44 and address.isalnum()

def save_wallet(message):
    user_id = str(message.from_user.id)
    wallet_address = message.text.strip()

    if not is_valid_wallet(wallet_address):
        bot.send_message(message.chat.id, "❌ Invalid wallet address. Please try again.")
        return

    if user_id not in data:
        data[user_id] = {
            "name": message.from_user.first_name,
            "username": f"@{message.from_user.username}" if message.from_user.username else "N/A",
            "referrals": 0,
            "joined": False,
            "wallet": "",
            "referred_by": ""
        }

    data[user_id]["wallet"] = wallet_address
    save_data()
    bot.send_message(message.chat.id, "✅ Wallet saved successfully!")

# ==== REFERRALS ====
@bot.message_handler(commands=['referrals'])
def show_referrals(message):
    user_id = str(message.from_user.id)
    count = data.get(user_id, {}).get("referrals", 0)
    bot.send_message(message.chat.id, f"👥 You referred {count}/5 users.")

# ==== POLLING START ====
#bot.remove_webhook()
bot.infinity_polling()
keep_alive()
