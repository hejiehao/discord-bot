import aiohttp
import discord
from discord import app_commands
from discord.app_commands import Choice
import json
import logging
import logging.handlers
import os
from typing import Optional
import urllib.parse

#Set up logging
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
logging.getLogger('discord.http').setLevel(logging.INFO)

handler = logging.handlers.RotatingFileHandler(
    filename='discord.log',
    encoding='utf-8',
    maxBytes=32 * 1024 * 1024,  # 32 MiB
    backupCount=5,  # Rotate through 5 files
)
dt_fmt = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
handler.setFormatter(formatter)
logger.addHandler(handler)

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        # A CommandTree is a special type that holds all the application command
        # state required to make it work. This is a separate class because it
        # allows all the extra state to be opt-in.
        # Whenever you want to work with application commands, your tree is used
        # to store and work with them.
        # Note: When using commands.Bot instead of discord.Client, the bot will
        # maintain its own tree instead.
        self.tree = app_commands.CommandTree(self)

    # This event is called when the bot is ready to start using application commands.
    async def setup_hook(self):
        await self.tree.sync()


intents = discord.Intents.default()
intents.message_content = True  # This makes the bot able to read message content
client = MyClient(intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')


@client.tree.command()
@app_commands.describe(
    first_value='第一个数字',
    second_value='第二个数字',
)
async def add(interaction: discord.Interaction, first_value: float, second_value: float):
    """把两个数字加在一起"""
    await interaction.response.send_message(f'{first_value} + {second_value} = {first_value + second_value}')
    
@client.tree.command()
@app_commands.describe(
    minuend='被减数',
    subtrahend='减数',
)
async def subtract(interaction: discord.Interaction, minuend: float, subtrahend: float):
    """把两个数字相减"""
    await interaction.response.send_message(f'{minuend} - {subtrahend} = {minuend - subtrahend}')


# The rename decorator allows us to change the display of the parameter on Discord.
# In this example, even though we use `text_to_send` in the code, the client will use `text` instead.
# Note that other decorators will still refer to it as `text_to_send` in the code.
@client.tree.command()
@app_commands.rename(text_to_send='text')
@app_commands.describe(text_to_send='你想要给当前频道发的消息')
async def send(interaction: discord.Interaction, text_to_send: str):
    """给当前频道发消息"""
    await interaction.response.send_message(text_to_send)


# To make an argument optional, you can either give it a supported default argument
# or you can mark it as Optional from the typing standard library. This example does both.
@client.tree.command()
@app_commands.describe(member='你想要查询加入时间的成员；默认为使用这个命令的人')
async def joined(interaction: discord.Interaction, member: Optional[discord.Member] = None):
    """查询指定成员的加入时间"""
    # If no member is explicitly provided then we use the command user here
    member = member or interaction.user

    # The format_dt function formats the date time into a human readable representation in the official client
    await interaction.response.send_message(f'{member} 在 {discord.utils.format_dt(member.joined_at)} 加入了这个服务器')


# A Context Menu command is an app command that can be run on a member or on a message by
# accessing a menu within the client, usually via right clicking.
# It always takes an interaction as its first parameter and a Member or Message as its second parameter.

# This context menu command only works on members
@client.tree.context_menu(name='查询加入时间')
async def show_join_date(interaction: discord.Interaction, member: discord.Member):
    # The format_dt function formats the date time into a human readable representation in the official client
    await interaction.response.send_message(f'{member} 在 {discord.utils.format_dt(member.joined_at)} 加入了这个服务器')

@client.tree.command()
async def hello(interaction: discord.Interaction):
    """打招呼！"""
    await interaction.response.send_message(f'你好, {interaction.user.mention}')
    
@client.tree.command()
async def ping(interaction: discord.Interaction):
    """ping pong"""
    await interaction.response.send_message('Pong！')
    
@client.tree.command()
@app_commands.describe(
    member="你想要谴责的人",
    content="你想要谴责的内容",
)
async def blame(interaction: discord.Interaction, member: discord.Member, content: str):
    """谴责一个人"""
    await interaction.response.send_message(f'我方对{content}表示强烈谴责。{content}是<@{member.id}>的蓄意行为，这种行为侵犯了我方的正当权益。我方要求<@{member.id}>立即停止{content}，并采取措施纠正错误。我方将继续密切关注此事的进展，并采取一切必要措施，以维护我方的正当权益。')


@client.tree.command()
@app_commands.describe(
    query="你想要搜索的词语",
    filter="筛选类型",
    mold="搜索方式",
)
@app_commands.choices(filter=[
    Choice(name="模组", value=1),
    Choice(name="整合包", value=2),
    Choice(name="资料", value=3),
    Choice(name="教程", value=4),
    Choice(name="作者", value=5),
    Choice(name="用户", value=6),
    Choice(name="社群", value=7),
],
                      mold=[
                          Choice(name="简单搜索", value=0),
                          Choice(name="复杂搜索", value=1),
                      ])
async def mcmod(interaction: discord.Interaction, query: str, mold: Optional[Choice[int]] = None, filter: Optional[Choice[int]] = None):
    """"在 MC 百科上搜索"""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://mcmod-api.zkitefly.eu.org/s/key={urllib.parse.quote(query)}{"&mold=0" if mold == None else f"&mold={mold.value}"}{"" if filter == None else f"&filter={filter.value}"}") as response:
            if response.status == 200:
                embed = []
                ret =json.loads(await response.text())
                for i in ret:
                    embed.append({
                        "type": "rich",
                        "url": i['address'],
                        "title": i['title'],
                        "description": i['description'],
                        "color": 0x94ff,
                        "timestamp": i['snapshot_time']
                    })
                await interaction.response.send_message(embeds=discord.Embed.from_dict(embed))
            else:
                await interaction.response.send_message("搜索失败，请检查你的输入。")

client.run(os.environ['TOKEN'], log_handler=None)
