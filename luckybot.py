from flask import Flask,request
import threading
import os
import telebot
from telebot import types
import random
import time
from datetime import datetime, timedelta
import json
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

app = Flask(__name__)

# Remplace par ton token et l'ID du canal
BOT_TOKEN = '7681705342:AAGLEW6bZ-2snBqGzqM44eRlysLqjY9WQwc'
CHANNEL_ID = '@mine1wgroup'  # ou '-1001234567890' pour un canal privé

# Dictionnaire pour stocker les cooldowns et les parrainages
user_cooldowns = {}
user_referrals = {}

# Route pour la page d'accueil
@app.route('/')
def home():
    return "Bot Telegram en ligne avec Flask!"

# Route pour gérer les webhooks de Telegram
@app.route('/webhook', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
    bot.process_new_updates([update])
    return 'ok', 200

def save_data():
    with open("user_data.json", "w") as file:
        json.dump({"referrals": user_referrals, "cooldowns": user_cooldowns}, file)

def load_data():
    global user_referrals, user_cooldowns
    try:
        with open("user_data.json", "r") as file:
            data = json.load(file)
            user_referrals = data.get("referrals", {})
            user_cooldowns = data.get("cooldowns", {})
    except FileNotFoundError:
        pass

load_data()


bot = telebot.TeleBot(BOT_TOKEN)

# Vérifier si l'utilisateur est abonné au canal
def check_subscription(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False

# Générer une prédiction aléatoire
def generate_prediction():
    min_mult = round(random.uniform(1.5, 5.0), 2)
    max_mult = round(min_mult + random.uniform(0.5, 1.5), 2)
    max_mult = min(max_mult, 15.0)
    from datetime import datetime, timezone
    current_time = datetime.now(timezone.utc)


    return min_mult, max_mult, current_time.strftime("%H:%M:%S"), (current_time + timedelta(seconds=60)).strftime("%H:%M:%S")

# Clavier personnalisé
def main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🤳Lancer la Prediction 🚀")
    markup.add("Règles", "1WIN", "🔗 Parrainage")
    return markup

def subscription_keyboard():
    markup = types.InlineKeyboardMarkup()
    check_button = types.InlineKeyboardButton("Check ✅", callback_data="check_subscription")
    markup.add(check_button)
    return markup


# Commande /start (gestion des parrainages incluse)
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    args = message.text.split()
    user_id = message.chat.id

 
    # Vérification de l'abonnement
    if not check_subscription(user_id):
        bot.send_message(
            message.chat.id, 
            f"🚀 Pour utiliser ce bot, rejoignez d'abord le canal 👉 {CHANNEL_ID} !\n\n"
            "Ensuite, cliquez sur le bouton Check ✅ pour confirmer votre abonnement.", 
            parse_mode='HTML',
            reply_markup=subscription_keyboard()
        )
        return

    # Initialisation du parrainage si l'utilisateur n'est pas encore enregistré
    if user_id not in user_referrals:
        user_referrals[user_id] = {'count': 0, 'bonus': 0}

    # Gestion du parrainage (si l'utilisateur a été invité)
    if len(args) > 1 and args[1].isdigit():
        referrer_id = int(args[1])
        if referrer_id != user_id and referrer_id in user_referrals:
            user_referrals[referrer_id]['count'] += 1
            if user_referrals[referrer_id]['count'] % 20 == 0:
                user_referrals[referrer_id]['bonus'] += 5
            bot.send_message(referrer_id, f"Un nouvel ami a rejoint grâce à vous ! 🎉\nTotal : {user_referrals[referrer_id]['count']}")
            save_data()

#  @bot.message_handler(commands=['start'])
# def send_welcome(message):
   
    
# Gestion du bouton "Check ✅"
@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def check_subscription_callback(call):
    user_id = call.from_user.id
    if check_subscription(user_id):
        bot.send_message(call.message.chat.id, "✅ Abonnement confirmé ! Vous pouvez maintenant utiliser le bot.", reply_markup=main_keyboard())
        bot.send_message(call.message.chat.id,"<b>LUKYJET PREDICTOR 2025 V1.0</b>\n\n"

                           "⚙️ les nouvelles technologies ont permis d'obtenir des cotes futures directement à partir du jeu Lucky Jet\n\n"     
                           "⚙️ administrator - @Minepro1w 🎰\n\n"
                          
                           "Clique sur 🤳Lancer la Prediction 🚀 pour avoir une prédiction 👇",
                   parse_mode='HTML', reply_markup=main_keyboard())

    else:
        bot.send_message(call.message.chat.id, f"❌ Vous n'êtes pas encore abonné à {CHANNEL_ID}. Rejoignez d'abord le canal et réessayez.", reply_markup=subscription_keyboard())
        
        
# Gestion des boutons
@bot.message_handler(content_types=['text'])
def handle_buttons(message):
    user_id = message.from_user.id
    if not check_subscription(user_id):
        bot.reply_to(message, f"Rejoignez d'abord {CHANNEL_ID} pour utiliser le bot !")
        return

    if message.text == "🤳Lancer la Prediction 🚀":
        if user_id in user_cooldowns and time.time() < user_cooldowns[user_id]:
            time_left = int(user_cooldowns[user_id] - time.time())
            bot.reply_to(message, f"<b> VEUILLEZ ATTENDRE {time_left} SECONDES AVANT LE PROCHAIN SIGNAL</b>\n\n"
                                  "1 - Pour gagner avec la prédiction, vous devez avoir un compte avec le code promo obligatoire <b>CASHF</b>.\n"
                                  "2 - Respectez les honoraires indiqués sur la prédiction.\n\n"
                                  "Voici le lien pour s'inscrire 👉https://1wzyuh.com/v3/lucky-jet-updated?p=himp",parse_mode='HTML')
            return

        min_mult, max_mult, start_time, end_time = generate_prediction()
        reliability = 90 + user_referrals.get(user_id, {'bonus': 0})['bonus']
        prediction_text = (
            "<b>NOUVEAU SIGNAL LUCKY JET</b>\n\n"
            " <b>PRÉDICTION</b>🚀\n"
            f"<b>     +{min_mult}x   〰️〰️   +{max_mult}x</b>\n\n"
            f"⏳<b> HEURE:</b> {start_time} - {end_time} GMT\n"
            f"<b>Fiabilité</b> : {reliability}%\n\n"
            "1 - Pour gagner avec la prédiction, vous devez avoir un compte avec le code promo obligatoire <b>CASHF</b>.\n"
            "2 - Respectez les honoraires indiqués sur la prédiction.\n\n"
            "Voici le lien pour s'inscrire 👉https://1wzyuh.com/v3/lucky-jet-updated?p=himp "
        )
        bot.send_message(message.chat.id, prediction_text, parse_mode='HTML')
        user_cooldowns[user_id] = time.time() + 110  # 2 minutes de cooldown

    elif message.text == "Règles":
        bot.send_message(message.chat.id,"📜<b> Comment ça marche ?</b>\n\n"
                              "<blockquote>1. Utilisez le bouton ''Lancer la prédiction'' pour obtenir un intervalle de cotes.</blockquote>\n\n"
                              "<blockquote>2. Encaissez dans cet intervalle pour maximiser vos gains .</blockquote>\n\n"
                              "<blockquote>3. Respectez le code promo <b>CASHF</b> lors de l'inscription pour accéder au faille.</blockquote>\n\n"
                              "<blockquote>4. Invitez des amis dans ''🔗 Parrainage'' pour augmenter la fiabilité des prédictions !</blockquote>",parse_mode='HTML')

    elif message.text == "1WIN":
        bot.reply_to(message, "Cliquez ici pour jouer 👉 https://1wzyuh.com/v3/lucky-jet-updated?p=himp ")

    elif message.text == "🔗 Parrainage":
        if user_id not in user_referrals:
          if user_id not in user_referrals:
             user_referrals[user_id] = {"count": 0, "bonus": 0}
        save_data()  # Sauvegarde après ajout
 # Initialise avec 0 parrainages
        ref_count = user_referrals[user_id]['count']
        bonus = user_referrals[user_id]['bonus']
        invite_link = f"https://t.me/{bot.get_me().username}?start={user_id}"
        referral_text = (
            f"👥 <b>Parrainage</b>\n\n"
            "<i>Invitez 20 amis pour augmenter la fiabilité de vos prédictions de 5% </i>!\n"
            f"- <b>Nombre d'invités</b> : {ref_count}\n"
            f"- <b>Votre ID</b> : {user_id}\n"
            f"- <b>Précision actuel</b> : {90 + bonus}%\n\n"
            f"<b>Votre lien d'invitation</b> : {invite_link}\n\n"
            "<blockquote><b>invitez 40 personne pour avoir une prédiction fiable à 100% </b></blockquote>"

        )
        bot.send_message(message.chat.id, referral_text, parse_mode='HTML')

# Fonction pour exécuter Flask en parallèle
def run_flask():
    app.run(host='0.0.0.0', port=8080)

# Démarrer le bot avec Flask
if __name__ == '__main__':
    # Supprimer le webhook existant
    bot.remove_webhook()
    
    # Définir le webhook avec l'URL de Render
    webhook_url =("https://lucky-bot-ce8w.onrender.com/webhook")  # L'URL du webhook, par exemple https://ton-app.render.com/webhook
    bot.set_webhook(url=webhook_url)
    
    # Lancer l'application Flask avec le port dynamique fourni par Render
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8080)))  # Utilisation du port dynamique
# Lancer le bot
# bot.polling()
# print("votre bot est lancé")
