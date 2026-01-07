import configparser
import sys

import dice
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

ROLL_COMMAND = '$roll'
@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith(ROLL_COMMAND):
        try:
            roll_cmd = message.content[len(ROLL_COMMAND):]
            roll = dice.roll(roll_cmd, raw=True)
            result = dice.utilities.verbose_print(roll)
        except:
            await message.channel.send('Rolls should be formatted like so: "$roll 2d6 + 1d100 + 69"')
        await message.channel.send(result)

client.run(BOT_TOKEN)
