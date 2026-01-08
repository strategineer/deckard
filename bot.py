import configparser
import datetime
import pprint
import sys
import sqlite3

import dice
import discord
from discord.ext import commands

def adapt_date_iso(val):
    """Adapt datetime.date to ISO 8601 date."""
    return val.isoformat()

def adapt_datetime_iso(val):
    """Adapt datetime.datetime to timezone-naive ISO 8601 date."""
    return val.replace(tzinfo=None).isoformat()

def adapt_datetime_epoch(val):
    """Adapt datetime.datetime to Unix timestamp."""
    return int(val.timestamp())

sqlite3.register_adapter(datetime.date, adapt_date_iso)
sqlite3.register_adapter(datetime.datetime, adapt_datetime_iso)
sqlite3.register_adapter(datetime.datetime, adapt_datetime_epoch)

def convert_date(val):
    """Convert ISO 8601 date to datetime.date object."""
    return datetime.date.fromisoformat(val.decode())

def convert_datetime(val):
    """Convert ISO 8601 datetime to datetime.datetime object."""
    return datetime.datetime.fromisoformat(val.decode())

def convert_timestamp(val):
    """Convert Unix epoch timestamp to datetime.datetime object."""
    return datetime.datetime.fromtimestamp(int(val))

sqlite3.register_converter("date", convert_date)
sqlite3.register_converter("datetime", convert_datetime)
sqlite3.register_converter("timestamp", convert_timestamp)

config = configparser.ConfigParser()
config.read('./secret/config.ini')


def load_secret(name):
    try:
        return config['Secrets'][name]
    except:
        print(f"Required {name} secret not found in config file, exiting")
        sys.exit(1)

BOT_TOKEN = load_secret('BotToken')
DB_PATH = load_secret('DBPath')
ADMIN_ID = load_secret('AdminID')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='$', intents=intents)

@bot.command()
async def roll(ctx, *args):
    arguments = ', '.join(args)
    try:
        roll = dice.roll(arguments, raw=True)
        result = dice.utilities.verbose_print(roll)
    except:
        await ctx.send('Rolls should be formatted like so: "$roll 2d6 + 1d100 + 69"')
        return
    await ctx.send(result)

@bot.group()
async def book(ctx):
    if ctx.invoked_subcommand is None:
        with sqlite3.connect(DB_PATH) as con:
            cur = con.cursor()
            # TODO only show rows after today, inclusive
            res = cur.execute("SELECT date(date), name from book order by date").fetchall()
            if res:
                await ctx.send(pprint.pformat(res))
            else:
                await ctx.send("No BookTalk books planned yet... :(")

@book.group()
async def idea(ctx):
    if ctx.invoked_subcommand is None:
        with sqlite3.connect(DB_PATH) as con:
            cur = con.cursor()
            res = cur.execute("SELECT date, name from bookidea order by date").fetchall()
            if res:
                await ctx.send(pprint.pformat(res))
            else:
                await ctx.send("No BookTalk book ideas planned yet... :(")

@idea.command()
async def add(ctx, idea_name):
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        data = (
            {"name": idea_name, "date": datetime.date.today()},
        )
        cur.executemany("INSERT INTO bookidea VALUES(:date, :name)", data)
        await ctx.send("Book idea added")

@book.command()
async def next(ctx):
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        res = cur.execute("SELECT name from book order by date LIMIT 1").fetchall()
        if res:
            await ctx.send(pprint.pformat(res))
        else:
            await ctx.send("No BookTalk books planned yet... :(")

def next_weekday(d, weekday, n_weeks):
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0: # Target day already happened this week
        days_ahead += 7
    return d + datetime.timedelta(days_ahead) + datetime.timedelta(days=7 * n_weeks)

@book.command()
async def add(ctx, book_name, n_weeks_from_now: int):
    if str(ctx.author.id) != ADMIN_ID:
        await ctx.send("You're not an admin!")
        return
    if n_weeks_from_now < 0:
        await ctx.send(f"n_weeks_from_now should be more than 0")
        return

    # Get next wednesday
    scheduled_day = next_weekday(datetime.date.today(), 2, n_weeks_from_now)
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        data = (
            {"name": book_name, "date": scheduled_day},
        )
        cur.executemany("INSERT INTO book VALUES(:date, :name)", data)
        await ctx.send("Book added")

@book.command()
async def edit(ctx, book_name, n_weeks_from_now: int, ):
    if str(ctx.author.id) != ADMIN_ID:
        await ctx.send("You're not an admin!")
        return
    if n_weeks_from_now < 0:
        await ctx.send(f"n_weeks_from_now should be more than 0")
        return

    # Get next wednesday
    scheduled_day = next_weekday(datetime.date.today(), 2, n_weeks_from_now)
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        data = (
            {"name": book_name, "date": scheduled_day},
        )
        cur.executemany("UPDATE book SET name = :name WHERE date = :date", data)
        await ctx.send("Book edited")

@book.command()
async def db_init(ctx):
    if str(ctx.author.id) != ADMIN_ID:
        await ctx.send("You're not an admin!")
        return
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute("CREATE TABLE book(date, name)")
        cur.execute("CREATE TABLE bookidea(date, name)")
    await ctx.send("Books table init-ed")

@book.command()
async def db_reset(ctx):
    if str(ctx.author.id) != ADMIN_ID:
        await ctx.send("You're not an admin!")
        return
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute("DROP TABLE book")
        cur.execute("DROP TABLE bookidea")
    await ctx.send("Books table reset")

@bot.event
async def on_ready():
    print(f'Machine Head ready to receive commmands!')

bot.run(BOT_TOKEN)
