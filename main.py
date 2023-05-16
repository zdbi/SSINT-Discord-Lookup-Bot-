import discord
from discord.ext import commands
import requests
from bs4 import BeautifulSoup
import ipinfo
from discord.gateway import DiscordWebSocket, _log
import sys
import asyncio
import time
from datetime import datetime, timedelta
import sqlite3
import random
import string
import json
import tls_client
import time
import aiohttp

bot = commands.Bot(command_prefix=",", intents=discord.Intents.all())
# bot invite - https://discord.com/api/oauth2/authorize?client_id=1105600239110475979&permissions=8&scope=bot
TOKEN = "MTEwODA3MDY1MDk5MzcwOTE5OA.GR7feE._K6j6vF3PCxADS_gvwT2YJj6au5cFB3g5TGa3g"
IPINFO_TOKEN = '4954fded41dfc0'
ROLE_ID = 1108071952268132363
session = tls_client.Session("chrome112")

def websocket(): #appear on mobile, delete if u dont want it ennit
    async def identify(self):
        payload = {
            'op': self.IDENTIFY,
            'd': {
                'token': self.token,
                'properties': {
                    '$os': sys.platform,
                    '$browser': 'Discord Android',
                    '$device': 'Discord Android',
                    '$referrer': '',
                    '$referring_domain': ''
                },
                'compress': True,
                'large_threshold': 250,
                'v': 3
            }
        }

        if self.shard_id is not None and self.shard_count is not None:
            payload['d']['shard'] = [self.shard_id, self.shard_count]

        state = self._connection
        if state._activity is not None or state._status is not None:
            payload['d']['presence'] = {
                'status': state._status,
                'game': state._activity,
                'since': 0,
                'afk': False
            }

        if state._intents is not None:
            payload['d']['intents'] = state._intents.value

        await self.call_hooks('before_identify', self.shard_id, initial=self._initial_identify)
        await self.send_as_json(payload)
        _log.info('Shard ID %s has sent the IDENTIFY payload.', self.shard_id)


    DiscordWebSocket.identify = identify

def get_badges(user):
    flags = user.public_flags
    badges = []

    if flags.staff:
        badges.append('Discord Staff')
    if flags.partner:
        badges.append('Partnered Server Owner')
    if flags.hypesquad:
        badges.append('HypeSquad Events')
    if flags.hypesquad_bravery:
        badges.append('HypeSquad Bravery')
    if flags.hypesquad_brilliance:
        badges.append('HypeSquad Brilliance')
    if flags.hypesquad_balance:
        badges.append('HypeSquad Balance')
    if flags.early_supporter:
        badges.append('Early Supporter')
    if flags.verified_bot_developer:
        badges.append('Verified Bot Developer')

    return badges

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="SSINT"))
    print(f'Ready to rape some niggas')
    conn = sqlite3.connect('keys.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS keys (
                    key TEXT PRIMARY KEY,
                    generated_by INTEGER,
                    generated_at TEXT,
                    redeemed_by INTEGER,
                    redeemed_at TEXT
                )''')
    conn.commit()
    conn.close()

def generate_key():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

def is_whitelisted():
    async def predicate(ctx):
        conn = sqlite3.connect('keys.db')
        c = conn.cursor()
        c.execute('SELECT * FROM keys WHERE redeemed_by=?', (ctx.author.id,))
        result = c.fetchone()
        conn.close()

        if result:
            return True
        else:
            raise commands.CheckFailure("You are not whitelisted to use this command.")

    return commands.check(predicate)




@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("You do not have permission to use this command.")
    else:
        raise error

@bot.command()
@commands.has_role(ROLE_ID)
async def create_key(ctx):
    key = generate_key()
    await ctx.reply(f"Check your private messages")
    await ctx.author.send(f'Your license key is: {key}')

    conn = sqlite3.connect('keys.db')
    c = conn.cursor()
    c.execute('INSERT INTO keys (key, generated_by, generated_at) VALUES (?, ?, ?)',
              (key, ctx.author.id, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()


@bot.command()
@commands.has_role(ROLE_ID)
async def delete_key(ctx, key):
    conn = sqlite3.connect('keys.db')
    c = conn.cursor()

    # Check if the key exists in the database
    c.execute('SELECT * FROM keys WHERE key = ?', (key,))
    result = c.fetchone()

    if result is not None:
        # Delete the key from the database
        c.execute('DELETE FROM keys WHERE key = ?', (key,))
        conn.commit()
        conn.close()
        await ctx.send(f"The key '{key}' has been successfully deleted.")
    else:
        conn.close()
        await ctx.send(f"The key '{key}' does not exist in the database.")



@bot.command()
async def redeem(ctx, key: str):
    if ctx.guild is not None:
        await ctx.message.delete()
        await ctx.send("Please send this command in a private message.", delete_after=10)
        return

    conn = sqlite3.connect('keys.db')
    c = conn.cursor()
    c.execute('SELECT key FROM keys WHERE key=? AND redeemed_by IS NULL', (key,))
    result = c.fetchone()

    if result:
        c.execute('UPDATE keys SET redeemed_by=?, redeemed_at=? WHERE key=?',
                  (ctx.author.id, datetime.utcnow().isoformat(), key))
        conn.commit()
        conn.close()
        await ctx.send("Key redeemed successfully.")
    else:
        conn.close()
        await ctx.send("Invalid key.")

@bot.command()
async def keyinfo(ctx, key: str):
    conn = sqlite3.connect('keys.db')
    c = conn.cursor()
    c.execute('SELECT * FROM keys WHERE key=?', (key,))
    result = c.fetchone()
    conn.close()
    role_color = ctx.author.color
    if result:
        key, generated_by, generated_at, redeemed_by, redeemed_at = result
        embed = discord.Embed(title=f"Key Information: {key}", color=role_color)

        embed.add_field(name="Generated By", value=f"<@{generated_by}>", inline=True)
        embed.add_field(name="Generated At", value=generated_at, inline=True)

        if redeemed_by:
            embed.add_field(name="Redeemed By", value=f"<@{redeemed_by}>", inline=True)
            embed.add_field(name="Redeemed At", value=redeemed_at, inline=True)
        else:
            embed.add_field(name="Redeemed By", value="Not redeemed", inline=True)
            embed.add_field(name="Redeemed At", value="Not redeemed", inline=True)
        embed.set_author(name=bot.user.name, icon_url=bot.user.display_avatar.url)
        await ctx.send(embed=embed)
    else:
        await ctx.send("Invalid key. Please try again.")

@bot.command()
@commands.has_role(ROLE_ID)
async def all_keys(ctx):
    conn = sqlite3.connect('keys.db')
    c = conn.cursor()
    c.execute('SELECT * FROM keys')
    all_keys = c.fetchall()
    conn.close()
    role_color = ctx.author.color
    embed = discord.Embed(title="All Generated Keys", color=role_color)

    for key, generated_by, generated_at, redeemed_by, redeemed_at in all_keys:
        key_info = f"Generated By: <@{generated_by}>\nGenerated At: {generated_at}\n"

        if redeemed_by:
            key_info += f"Redeemed By: <@{redeemed_by}>\nRedeemed At: {redeemed_at}"
        else:
            key_info += "Not redeemed"

        embed.add_field(name=f"Key: {key}", value=key_info, inline=False)
    embed.set_author(name=bot.user.name, icon_url=bot.user.display_avatar.url)
    await ctx.send(embed=embed)


@bot.command()
@is_whitelisted()
async def iplookup(ctx, ip: str): #IP lookup
    role_color = ctx.author.color
    async with aiohttp.ClientSession() as session:
        url = f'https://search.illicit.services/records?ips={ip}'
        async with session.get(url) as response:
            if response.status == 200:
                html = await response.text()

                # Parse HTML and extract <dd> elements
                soup = BeautifulSoup(html, 'html.parser')
                dd_elements = soup.find_all('dd')
                data = [el.get_text() for el in dd_elements]  # el.get_text() gets only the text within the <dd> tags

                # Create the embed
                embed = discord.Embed(title="IP Lookup", description=f"Information for IP: {ip}", color=role_color)

                # Add each line as a field in the embed, excluding the "source" field
                for line in data:
                    if ':' in line:
                        title, value = line.split(':', 1)
                        title = title.strip().capitalize()  # Capitalize the field title
                        value = value.strip()

                        # Only add the field to the embed if the title is not "source"
                        if title.lower() != "source":
                            embed.add_field(name=f"{title}:", value=value, inline=False)
                embed.set_author(name=bot.user.name, icon_url=bot.user.display_avatar.url)
                await ctx.send(embed=embed)
            else:
                await ctx.send('Unable to fetch data from the website.')



@bot.command()
@is_whitelisted()
async def emaillookup(ctx, email: str): #Email lookup
    role_color = ctx.author.color

    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36'
    }

    try:
        data = session.get(f'https://search.illicit.services/records?emails={email}&wt=json', headers=headers)
    except:
        await ctx.send(f'Error getting email info!')
        return

    embed = discord.Embed(title=f'__Email Lookup for "{email}"__', color=role_color)

    embed.add_field(name='**__Results__**', value=f'`{data.json()["resultCount"]}`', inline=True)
    embed.add_field(name='**__Records__**', value=f'`In the attached text file.`', inline=True)
    embed.set_author(name=bot.user.name, icon_url=bot.user.display_avatar.url)
    await ctx.send(embed=embed)
    
    with open('records.txt', 'w') as f:
        f.write(json.dumps(data.json()["records"], indent=4))

    with open('records.txt', 'rb') as f:
        await ctx.send(file=discord.File(f, 'records.txt'))

@bot.command()
@is_whitelisted()
async def userinfo(ctx, user_id: int):
    role_color = ctx.author.color
    try:
        user = await bot.fetch_user(user_id)

        if user:
            embed = discord.Embed(title=f'__Information for User ID "{user_id}"__', color=role_color)
            embed.set_author(name=bot.user.name, icon_url=bot.user.display_avatar.url)
            embed.add_field(name='User ID', value=user.id, inline=True)
            embed.add_field(name='Username', value=f'{user.name}#{user.discriminator}', inline=True)
            embed.add_field(name='Account Creation Date', value=user.created_at.strftime('%Y-%m-%d %H:%M:%S UTC'), inline=True)
            embed.add_field(name='Badges', value=', '.join(get_badges(user)) or 'None', inline=True)

            embed.set_thumbnail(url=user.avatar.url)

            if user.banner:
                embed.set_image(url=user.banner.url)

            await ctx.send(embed=embed)
        else:
            await ctx.send(f'User not found. Please provide a valid user ID.')

    except Exception as e:
        print(e)
        await ctx.send(f'Error getting user information! Exception: {e}')



@bot.command()
async def clear_dms(ctx):
    if ctx.guild is not None:
        await ctx.message.delete()
        await ctx.send("Please send this command in a private message.", delete_after=10)
        return

    async for message in ctx.channel.history(limit=1000):
        if message.author == bot.user:
            await message.delete()

@bot.command()
@is_whitelisted()
async def spotify(ctx):
    role_color = ctx.author.color
    embed = discord.Embed(title=f"", color=role_color)
    embed.set_author(name=bot.user.name, icon_url=bot.user.display_avatar.url)
    embed.add_field(name='Step 1', value="> To get an email from a spotify account you must go to https://support.spotify.com/us/contact-spotify-support/ (click start messaging)", inline=False)
    embed.add_field(name='Step 2', value="> Then what you must do is give them the spotify account you are trying to get intel on and request for the partial email", inline=False)
    embed.add_field(name='Step 3', value="> Some responders might say that they aren't allowed to give out the information, if they do this request to talk to their supervisor", inline=False)


    await ctx.send(embed=embed)

@bot.command()
@is_whitelisted()
async def swat(ctx):
    # Open the Notepad file
    with open('swatmethod.txt', 'rb') as file:
        # Create a discord.File object from the file
        notepad_file = discord.File(file, filename='swatmethod.txt')
        # Send the file as an attachment
        await ctx.send(file=notepad_file)

@bot.command()
@is_whitelisted()
async def andriod(ctx):
    # Open the Notepad file
    with open('andriod.txt', 'rb') as file:
        # Create a discord.File object from the file
        notepad_file = discord.File(file, filename='andriod.txt')
        # Send the file as an attachment
        await ctx.send(file=notepad_file)

@bot.command()
@is_whitelisted()
async def safe(ctx):
    role_color = ctx.author.color
    embed = discord.Embed(title=f"", color=role_color)
    embed.set_author(name=bot.user.name, icon_url=bot.user.display_avatar.url)
    embed.add_field(name='Step 1', value="> Get a good VPN provider such as Mullvad or PIA and ALWAYS keep it on. (if you're on mobile, go to the app store and download a VPN)", inline=False)
    embed.add_field(name='Step 2', value="> Get a good virus protector such as AVG to stop you from going onto malicious sites and downloading malicious files.", inline=False)
    embed.add_field(name='Step 3', value="> Check if something is safe to download before downloading it. https://www.malwarebytes.com/", inline=False)
    embed.add_field(name='Step 4', value="> DON'T EDATE (this is cause for online trust that can lead to persec failures, people have been known to date people just for info)", inline=False)
    embed.add_field(name='Step 5', value="> Don't give out personal information (name, number, emails, state/city, DOB, family info, ETC.) a country and age is okay.", inline=False)
    embed.add_field(name='Step 6', value="> Don't show your face to ANYONE (if you edate, it's better to catfish than to get doxed)", inline=False)
    await ctx.send(embed=embed)

@bot.command()
@is_whitelisted()
async def opsec(ctx):
    role_color = ctx.author.color
    embed = discord.Embed(title=f"", color=role_color)
    embed.set_author(name=bot.user.name, icon_url=bot.user.display_avatar.url)
    embed.add_field(name='Defintion', value="> Operations Security is the systematic and proven process that means protecting your online information.", inline=False)
    await ctx.send(embed=embed)

@bot.command()
@is_whitelisted()
async def persec(ctx):
    role_color = ctx.author.color
    embed = discord.Embed(title=f"", color=role_color)
    embed.set_author(name=bot.user.name, icon_url=bot.user.display_avatar.url)
    embed.add_field(name='Defintion', value="> The Personnel Security (PerSec) Program upholds the standards, criteria, and guidelines upon which determines how safe your personal information is such as name, number, address, etc.", inline=False)
    await ctx.send(embed=embed)

@bot.command()
@is_whitelisted()
async def osint(ctx):
    role_color = ctx.author.color
    embed = discord.Embed(title=f"", color=role_color)
    embed.set_author(name=bot.user.name, icon_url=bot.user.display_avatar.url)
    embed.add_field(name='Defintion', value="> Open Source Intelligence is the ability to get public personal information such as a name, number, address, etc.", inline=False)
    await ctx.send(embed=embed)

@bot.command()
@is_whitelisted()
async def csint(ctx):
    role_color = ctx.author.color
    embed = discord.Embed(title=f"", color=role_color)
    embed.set_author(name=bot.user.name, icon_url=bot.user.display_avatar.url)
    embed.add_field(name='Defintion', value="> Closed Source Intelligence is the ability to get private personal information such as an SSN, Credit Card Number, License, ETC.", inline=False)
    await ctx.send(embed=embed)

@bot.command()
@is_whitelisted()
async def skid(ctx):
    role_color = ctx.author.color
    embed = discord.Embed(title=f"", color=role_color)
    embed.set_author(name=bot.user.name, icon_url=bot.user.display_avatar.url)
    embed.add_field(name='Defintion', value="> Someone who can't code or steals code from others", inline=False)
    await ctx.send(embed=embed)

@bot.command()
@is_whitelisted()
async def larp(ctx):
    role_color = ctx.author.color
    embed = discord.Embed(title=f"", color=role_color)
    embed.set_author(name=bot.user.name, icon_url=bot.user.display_avatar.url)
    embed.add_field(name='Defintion', value="> Someone pretending to be something they aren't", inline=False)
    await ctx.send(embed=embed)

@bot.command()
@is_whitelisted()
async def pentagon(ctx):
    role_color = ctx.author.color
    embed = discord.Embed(title=f"", color=role_color)
    embed.set_author(name=bot.user.name, icon_url=bot.user.display_avatar.url)
    embed.add_field(name='Website', value="> https://ibb.co/album/nqsvTJ", inline=False)
    await ctx.send(embed=embed)

@bot.command()
@is_whitelisted()
async def stfu(ctx):
    role_color = ctx.author.color
    embed = discord.Embed(title=f"", color=role_color)
    embed.set_author(name=bot.user.name, icon_url=bot.user.display_avatar.url)
    embed.add_field(name='stfu', value="> we muzzle the monkeys, not backwards", inline=False)
    await ctx.send(embed=embed)

@bot.command(name='coordinates')
@is_whitelisted()
async def coordinates(ctx, lat: float, long: float):
    async with aiohttp.ClientSession() as session:
        url = f'https://search.illicit.services/spatial?latLong={lat},{long}'
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.text()

                with open('coordinates_data.txt', 'w', encoding='utf-8') as file:
                    file.write(data)

                with open('coordinates_data.txt', 'rb') as file:
                    await ctx.send(file=discord.File(file, 'coordinates_data.txt'))
            else:
                await ctx.send('Unable to fetch data from the website.')

websocket()
bot.run(TOKEN)
