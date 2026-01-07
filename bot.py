import configparser
import sys

import discord

config = configparser.ConfigParser()
config.read('./secret/config.ini')

try:
    BOT_TOKEN = config['Secrets']['BotToken']
except:
    print('Required BOT_TOKEN secret not found in config file, exiting')
    sys.exit(1)

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

client.run(BOT_TOKEN)
