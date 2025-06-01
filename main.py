import telebot
from telebot import types
import os
import json

# ==== CONFIG ====
BOT_TOKEN = '7329361068:AAE7-6u7RC0jqouIvLAdpaV6xtjXWJEcN-w'
GROUP_ID = -1002534069646
GROUP_LINK = "https://t.me/TTNCoin"
bot = telebot.TeleBot(BOT_TOKEN)

# ==== FILE PATH (FIXED FOR RENDER) ====
DATA_FILE = "user_data.json"

# ==== INIT DATA ====
data = {}
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        data = json.load(f)


def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


# ==== START ====
@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    user_name = message.from_user.first_name
    username = message.from_user.username or ""

    if user_id not in data:
        data[user_id] = {
            "name": user_name,
            "username": f"@{username}" if username else "N/A",
            "referrals": [],
            "joined": False,
            "wallet": ""
        }
    else:
        data[user_id]["name"] = user_name
        data[user_id]["username"] = f"@{username}" if username else "N/A"

    # REFERRAL HANDLER
    args = message.text.split()
    if len(args) > 1:
        referrer = args[1]
        if referrer != user_id and user_id not in data.get(referrer, {}).get("referrals", []):
            if referrer not in data:
                data[referrer] = {
                    "name": "",
                    "username": "",
                    "referrals": [],
                    "joined": False,
                    "wallet": ""
                }
            data[referrer]["referrals"].append(user_id)

    # GROUP CHECK
    try:
        member = bot.get_chat_member(GROUP_ID, message.from_user.id)
        data[user_id]["joined"] = member.status in ['member', 'creator', 'administrator']
    except:
        data[user_id]["joined"] = False

    save_data()

    referral_link = f"https://t.me/{bot.get_me().username}?start={user_id}"
    count = len(data[user_id]["referrals"])
    joined = "✅" if data[user_id]["joined"] else "❌"
    wallet = "✅" if data[user_id]["wallet"] else "❌"

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📣 Share Referral", switch_inline_query=referral_link))
    markup.add(types.InlineKeyboardButton("👥 Join Our Group", url=GROUP_LINK))
    markup.add(types.InlineKeyboardButton("🔗 Connect Wallet", callback_data="connect_wallet"))

    bot.send_message(message.chat.id, f"👋 Welcome {user_name}!\n\n"
                     f"💰 Referral link:\n{referral_link}\n\n"
                     f"👥 Referred: {count}/5\n"
                     f"📢 Group Joined: {joined}\n"
                     f"🔗 Wallet: {wallet}", reply_markup=markup)


# ==== /referrals ====
@bot.message_handler(commands=['referrals'])
def show_referrals(message):
    user_id = str(message.from_user.id)
    referred = data.get(user_id, {}).get("referrals", [])

    if not referred:
        bot.send_message(message.chat.id, "😕 No referrals yet.")
    else:
        msg = f"👥 You referred {len(referred)} users:\n"
        for uid in referred:
            name = data.get(uid, {}).get("name", "Unknown")
            username = data.get(uid, {}).get("username", "N/A")
            msg += f"• {name} ({username}) — [ID: {uid}]\n"
        bot.send_message(message.chat.id, msg)


# ==== Wallet Connect ====
@bot.callback_query_handler(func=lambda call: call.data == "connect_wallet")
def ask_wallet(call):
    bot.send_message(call.message.chat.id, "🔐 Send your Phantom wallet address:")
    bot.register_next_step_handler(call.message, save_wallet)


def save_wallet(message):
    user_id = str(message.from_user.id)
    wallet_address = message.text.strip()

    # Simple Validation (Phantom starts with A or B and is ~44 chars)
    if not (wallet_address.startswith("A") or wallet_address.startswith("B")) or len(wallet_address) < 30:
        bot.send_message(message.chat.id, "❌ Invalid wallet address. Please try again.")
        return

    if user_id not in data:
        data[user_id] = {
            "name": message.from_user.first_name,
            "username": f"@{message.from_user.username}" if message.from_user.username else "N/A",
            "referrals": [],
            "joined": False,
            "wallet": ""
        }

    data[user_id]["wallet"] = wallet_address
    save_data()
    bot.send_message(message.chat.id, "✅ Wallet saved successfully!")


# ==== /mydata (DEBUG COMMAND) ====
@bot.message_handler(commands=['mydata'])
def my_data(message):
    user_id = str(message.from_user.id)
    user = data.get(user_id, {})
    bot.send_message(message.chat.id, json.dumps(user, indent=4))


# ==== BOT RUN ====
bot.infinity_polling()
