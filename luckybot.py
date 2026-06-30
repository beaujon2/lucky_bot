import asyncio
import logging
import random
import json
import time

from datetime import datetime, timedelta, timezone
from aiohttp import web
import threading

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton,
)
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# ═══════════════════════════════════════════════════
#  CONFIG  👇 Remplace ces valeurs
# ═══════════════════════════════════════════════════
BOT_TOKEN    = "7681705342:AAECmNfwrXMkrdYJkNYjLX-MfCsqILF32Hs"
CHANNEL_ID   = "@mine1wgroup"
CHANNEL_LINK = "https://t.me/mine1wgroup"
AFFILIATE_LINK = "https://1wzyuh.com/v3/lucky-jet-updated?p=himp"
ADMIN_USERNAME = "@Minepro1w"
DATA_FILE    = "user_data.json"
COOLDOWN_SEC = 110   # secondes entre deux prédictions
# ═══════════════════════════════════════════════════

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp  = Dispatcher(storage=MemoryStorage())

# ═══════════════════════════════════════════════════
#  DONNÉES UTILISATEURS (JSON)
# ═══════════════════════════════════════════════════
user_referrals: dict = {}   # {user_id: {"count": int, "bonus": int}}
user_cooldowns: dict = {}   # {user_id: timestamp_fin_cooldown}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump({"referrals": user_referrals, "cooldowns": user_cooldowns}, f)

def load_data():
    global user_referrals, user_cooldowns
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            user_referrals = {int(k): v for k, v in data.get("referrals", {}).items()}
            user_cooldowns = {int(k): v for k, v in data.get("cooldowns", {}).items()}
    except FileNotFoundError:
        pass

load_data()

# ═══════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════
async def check_subscription(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status not in ("left", "kicked", "banned")
    except Exception:
        return False

def generate_prediction():
    min_mult = round(random.uniform(1.5, 5.0), 2)
    max_mult = round(min_mult + random.uniform(0.5, 1.5), 2)
    max_mult = min(max_mult, 15.0)
    now = datetime.now(timezone.utc)
    start = now.strftime("%H:%M:%S")
    end   = (now + timedelta(seconds=60)).strftime("%H:%M:%S")
    return min_mult, max_mult, start, end

def ensure_user(user_id: int):
    if user_id not in user_referrals:
        user_referrals[user_id] = {"count": 0, "bonus": 0}

# ═══════════════════════════════════════════════════
#  KEYBOARDS
# ═══════════════════════════════════════════════════
def main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🤳 Lancer la Prediction 🚀")],
            [KeyboardButton(text="Règles"), KeyboardButton(text="1WIN"), KeyboardButton(text="🔗 Parrainage")],
        ],
        resize_keyboard=True
    )

def subscription_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Rejoindre le canal", url=CHANNEL_LINK)],
        [InlineKeyboardButton(text="Check ✅", callback_data="check_subscription")],
    ])

# ═══════════════════════════════════════════════════
#  /start
# ═══════════════════════════════════════════════════
@dp.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    args = message.text.split()

    ensure_user(user_id)

    # Gestion parrainage
    if len(args) > 1 and args[1].isdigit():
        referrer_id = int(args[1])
        if referrer_id != user_id and referrer_id in user_referrals:
            user_referrals[referrer_id]["count"] += 1
            if user_referrals[referrer_id]["count"] % 20 == 0:
                user_referrals[referrer_id]["bonus"] += 5
            await bot.send_message(
                referrer_id,
                f"🎉 Un nouvel ami a rejoint grâce à vous !\n"
                f"Total invités : <b>{user_referrals[referrer_id]['count']}</b>"
            )
            save_data()

    # Vérification abonnement
    if not await check_subscription(user_id):
        await message.answer(
            f"🚀 Pour utiliser ce bot, rejoignez d'abord le canal 👉 {CHANNEL_LINK} !\n\n"
            "Ensuite, cliquez sur le bouton <b>Check ✅</b> pour confirmer votre abonnement.",
            reply_markup=subscription_keyboard()
        )
        return

    await message.answer(
        "<b>LUKYJET PREDICTOR 2025 V1.0</b>\n\n"
        "⚙️ Les nouvelles technologies ont permis d'obtenir des cotes futures directement à partir du jeu Lucky Jet\n\n"
        f"⚙️ Administrateur - {ADMIN_USERNAME} 🎰\n\n"
        "Clique sur 🤳 Lancer la Prediction 🚀 pour avoir une prédiction 👇",
        reply_markup=main_keyboard()
    )

# ═══════════════════════════════════════════════════
#  CALLBACK — Check abonnement
# ═══════════════════════════════════════════════════
@dp.callback_query(F.data == "check_subscription")
async def on_check_subscription(call: CallbackQuery):
    user_id = call.from_user.id
    ensure_user(user_id)

    if not await check_subscription(user_id):
        await call.answer(
            f"❌ Vous n'êtes pas encore abonné. Rejoignez le canal et réessayez.",
            show_alert=True
        )
        return

    await call.answer()
    await call.message.delete()
    await bot.send_message(
        call.message.chat.id,
        "✅ Abonnement confirmé ! Vous pouvez maintenant utiliser le bot.",
        reply_markup=main_keyboard()
    )
    await bot.send_message(
        call.message.chat.id,
        "<b>LUKYJET PREDICTOR 2025 V1.0</b>\n\n"
        "⚙️ Les nouvelles technologies ont permis d'obtenir des cotes futures directement à partir du jeu Lucky Jet\n\n"
        f"⚙️ Administrateur - {ADMIN_USERNAME} 🎰\n\n"
        "Clique sur 🤳 Lancer la Prediction 🚀 pour avoir une prédiction 👇",
        reply_markup=main_keyboard()
    )

# ═══════════════════════════════════════════════════
#  HANDLER MENU
# ═══════════════════════════════════════════════════
@dp.message(F.text)
async def handle_buttons(message: Message):
    user_id = message.from_user.id

    # Vérif abonnement à chaque action
    if not await check_subscription(user_id):
        await message.answer(
            f"❌ Rejoignez d'abord {CHANNEL_LINK} pour utiliser le bot !",
            reply_markup=subscription_keyboard()
        )
        return

    ensure_user(user_id)

    # ── PREDICTION ──
    if message.text == "🤳 Lancer la Prediction 🚀":
        now = time.time()
        cooldown_end = user_cooldowns.get(user_id, 0)

        if now < cooldown_end:
            time_left = int(cooldown_end - now)
            await message.answer(
                f"<b>⏳ VEUILLEZ ATTENDRE {time_left} SECONDES AVANT LE PROCHAIN SIGNAL</b>\n\n"
                "1 - Pour gagner avec la prédiction, vous devez avoir un compte avec le code promo obligatoire <b>CASHF</b>.\n"
                "2 - Respectez les honoraires indiqués sur la prédiction.\n\n"
                f"Voici le lien pour s'inscrire 👉 {AFFILIATE_LINK}"
            )
            return

        min_mult, max_mult, start_time, end_time = generate_prediction()
        reliability = 90 + user_referrals[user_id]["bonus"]

        await message.answer(
            "<b>🚀 NOUVEAU SIGNAL LUCKY JET</b>\n\n"
            "✈️ <b>PRÉDICTION</b>\n"
            f"<b>     +{min_mult}x   〰️〰️   +{max_mult}x</b>\n\n"
            f"⏳ <b>HEURE:</b> {start_time} - {end_time} GMT\n"
            f"🎯 <b>Fiabilité</b> : {reliability}%\n\n"
            "1 - Pour gagner avec la prédiction, vous devez avoir un compte avec le code promo obligatoire <b>CASHF</b>.\n"
            "2 - Respectez les honoraires indiqués sur la prédiction.\n\n"
            f"Voici le lien pour s'inscrire 👉 {AFFILIATE_LINK}"
        )
        user_cooldowns[user_id] = now + COOLDOWN_SEC
        save_data()

    # ── RÈGLES ──
    elif message.text == "Règles":
        await message.answer(
            "📜 <b>Comment ça marche ?</b>\n\n"
            "<blockquote>1. Utilisez le bouton <b>Lancer la prédiction</b> pour obtenir un intervalle de cotes.</blockquote>\n\n"
            "<blockquote>2. Encaissez dans cet intervalle pour maximiser vos gains.</blockquote>\n\n"
            "<blockquote>3. Respectez le code promo <b>CASHF</b> lors de l'inscription pour accéder à la faille.</blockquote>\n\n"
            "<blockquote>4. Invitez des amis via <b>🔗 Parrainage</b> pour augmenter la fiabilité des prédictions !</blockquote>"
        )

    # ── 1WIN ──
    elif message.text == "1WIN":
        await message.answer(
            f"Cliquez ici pour jouer 👉 {AFFILIATE_LINK}"
        )

    # ── PARRAINAGE ──
    elif message.text == "🔗 Parrainage":
        ref_count = user_referrals[user_id]["count"]
        bonus     = user_referrals[user_id]["bonus"]
        bot_info  = await bot.get_me()
        invite_link = f"https://t.me/{bot_info.username}?start={user_id}"

        await message.answer(
            f"👥 <b>Parrainage</b>\n\n"
            "<i>Invitez 20 amis pour augmenter la fiabilité de vos prédictions de 5% !</i>\n\n"
            f"- <b>Nombre d'invités</b> : {ref_count}\n"
            f"- <b>Votre ID</b> : {user_id}\n"
            f"- <b>Précision actuelle</b> : {90 + bonus}%\n\n"
            f"<b>Votre lien d'invitation :</b>\n{invite_link}\n\n"
            "<blockquote><b>Invitez 40 personnes pour avoir une prédiction fiable à 100% !</b></blockquote>"
        )

# ═══════════════════════════════════════════════════
#  SERVEUR WEB (keep-alive pour Render)
# ═══════════════════════════════════════════════════
def run_web():
    async def handle(request):
        return web.Response(text="Lucky Jet Bot en ligne !")
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    loop = asyncio.new_event_loop()
    loop.run_until_complete(runner.setup())
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    loop.run_until_complete(site.start())
    loop.run_forever()

threading.Thread(target=run_web, daemon=True).start()

# ═══════════════════════════════════════════════════
#  DÉMARRAGE
# ═══════════════════════════════════════════════════
async def main():
    # Supprimer le webhook avant de démarrer le polling
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("🚀 Lucky Jet Bot démarré !")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
