import requests
from env import *
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio
import logging




logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


application = Application.builder().token(BOT_TOKEN).build()


async def sendAlert(onlinePlayers):
    try:
        message = (
            f"🚨 ALERT!\n"
            f"👥 Ci sono {onlinePlayers} giocatori connessi\n"
            f"🌐 Server: {SERVER_IP}\n"
            f"🚀 Entra ora! ⚡"
        )

        await application.bot.send_message(
            chat_id=GROUP_ID,
            text=message
        )
        logger.info(f"Alert inviato a {GROUP_ID}: {onlinePlayers} giocatori")

    except Exception as e:
        logger.error(f"Errore nell'invio alert: {e}")


async def players_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /players che restituisce il numero di giocatori"""
    try:
        onlinePlayers = getPlayers()

        chat_id = update.message.chat.id
        logger.info(f"Comando /players ricevuto da chat_id: {chat_id}")

        message = (
            f"🌐 **Server**: {SERVER_IP}\n"
            f"👥 **Giocatori**: {onlinePlayers}"
        )

        await update.message.reply_text(message, parse_mode='Markdown')
        logger.info(f"Risposto a /players: {onlinePlayers} giocatori")

    except Exception as e:
        logger.error(f"Errore in players_command: {e}")
        await update.message.reply_text("❌ Errore nel recuperare i dati del server")


def getPlayers():
    try:
        logger.info(f"Controllo server: {SERVER_IP}")
        response = requests.get(f"https://api.mcsrvstat.us/3/{SERVER_IP}", timeout=10).json()

        if response.get("online", False):
            online_players = response["players"]["online"]
            logger.info(f"Server online - Giocatori: {online_players}")
            return online_players
        else:
            logger.warning("Server offline")
            return 0

    except Exception as e:
        logger.error(f"Errore nel controllo server: {e}")
        return 0


async def monitoring_loop():
    """Loop di monitoraggio separato"""
    last_alert_players = 0 #temp var
    logger.info("🤖 Monitoraggio avviato!")
    logger.info(f"🌐 Server: {SERVER_IP}")
    logger.info(f"👥 Soglia: {MIN_PLAYERS}+ giocatori")
    logger.info(f"📨 Group ID: {GROUP_ID}")


    while True:
        try:
            onlinePlayers = getPlayers()

            if onlinePlayers >= MIN_PLAYERS and onlinePlayers != last_alert_players:

                await sendAlert(onlinePlayers)
                last_alert_players = onlinePlayers
            elif onlinePlayers < MIN_PLAYERS:
                last_alert_players = 0

            await asyncio.sleep(300)

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Errore nel monitoring_loop: {e}")
            await asyncio.sleep(60)


async def main():
    """Funzione principale"""
    try:

        application.add_handler(CommandHandler("players", players_command))

        #Starting the bot
        await application.initialize()
        await application.start()
        await application.updater.start_polling()


        monitoring_task = asyncio.create_task(monitoring_loop())
        await asyncio.Future()

    except KeyboardInterrupt:
        logger.info("Bot fermato dall'utente")
    except Exception as e:
        logger.error(f"Errore nel main: {e}")
    finally:
        #Quit safely
        if 'monitoring_task' in locals():
            monitoring_task.cancel()
            try:
                await monitoring_task
            except asyncio.CancelledError:
                pass

        try:
            await application.updater.stop()
            await application.stop()
            await application.shutdown()
        except:
            pass


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot terminato")
    except Exception as e:
        print(f"Errore critico: {e}")