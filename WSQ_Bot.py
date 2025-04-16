import discord
from discord.ext import commands
from discord import app_commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import asyncio
import pytz
from datetime import datetime

import os
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True

# Ustawienie globalnych allowed_mentions, dzięki czemu bot może wzmiankować @everyone
allowed_mentions = discord.AllowedMentions(everyone=True)

# Używamy prefixu '/' oraz podajemy allowed_mentions przy tworzeniu bota
bot = commands.Bot(command_prefix="/", intents=intents, allowed_mentions=allowed_mentions)
tree = bot.tree

scheduler = AsyncIOScheduler()

# Domyślne ustawienia – zmieniane przez komendy
default_channel_id = None
message_text = "@everyone Grać cholery!"
scheduled_hour = 19
scheduled_minute = 0

def schedule_daily_message():
    # Usuwamy poprzednie zadania, by uniknąć duplikatów
    scheduler.remove_all_jobs()
    trigger = CronTrigger(hour=scheduled_hour, minute=scheduled_minute, timezone='Europe/Warsaw')
    scheduler.add_job(send_scheduled_message, trigger)
    print(f"Scheduled job set for {scheduled_hour:02d}:{scheduled_minute:02d} (czasu polskiego)")

async def send_scheduled_message():
    print("PRÓBA WYSŁANIA WIADOMOŚCI")
    if default_channel_id is None:
        print("Nie ustawiono kanału do wysyłki.")
        return
    channel = bot.get_channel(default_channel_id)
    if channel:
        print("Kanał znaleziony. Wysyłam wiadomość...")
        await channel.send(message_text, allowed_mentions=discord.AllowedMentions(everyone=True))
    else:
        print("Nie znaleziono kanału. Upewnij się, że wywołałeś komendę `/setchannel`.")

@bot.event
async def on_ready():
    global default_channel_id
    print(f"Zalogowano jako {bot.user}")
    scheduler.start()
    schedule_daily_message()
    synced = await tree.sync()
    print(f"Zsynchronizowano {len(synced)} komend slash.")
    print("Bot gotowy. Kanał domyślny:", default_channel_id)

@tree.command(name="settext", description="Ustaw treść wiadomości")
@app_commands.describe(tresc="Nowa treść wiadomości (może zawierać @everyone)")
async def settext(interaction: discord.Interaction, tresc: str):
    global message_text
    message_text = tresc
    await interaction.response.send_message(f"Treść ustawiona na:\n`{message_text}`")
    print("Nowa treść wiadomości ustawiona:", message_text)

@tree.command(name="settime", description="Ustaw godzinę wiadomości w formacie HH:MM (24h)")
@app_commands.describe(czas="Godzina w formacie 19:00")
async def settime(interaction: discord.Interaction, czas: str):
    global scheduled_hour, scheduled_minute
    try:
        hour, minute = map(int, czas.strip().split(":"))
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError
        scheduled_hour = hour
        scheduled_minute = minute
        schedule_daily_message()
        await interaction.response.send_message(f"Czas wiadomości ustawiony na {hour:02d}:{minute:02d} (czasu polskiego)")
        print(f"Czas wiadomości ustawiony na {hour:02d}:{minute:02d}")
    except ValueError:
        await interaction.response.send_message("Nieprawidłowy format czasu. Użyj formatu HH:MM, np. 19:00")

@tree.command(name="setchannel", description="Ustaw kanał do wysyłania wiadomości")
async def setchannel(interaction: discord.Interaction):
    global default_channel_id
    default_channel_id = interaction.channel.id
    await interaction.response.send_message("Ten kanał został ustawiony jako domyślny do wysyłki wiadomości.")
    print("Default channel ustawiony:", default_channel_id)

bot.run(TOKEN)
