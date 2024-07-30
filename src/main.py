from typing import Optional
import discord
from discord import app_commands
from discord.ext import commands
import logging
import logging.handlers
import os

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


MY_GUILD = discord.Object(id=os.environ['GUILD_ID'])  # replace with your guild id


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

    # In this basic example, we just synchronize the app commands to one guild.
    # Instead of specifying a guild to every command, we copy over our global commands instead.
    # By doing so, we don't have to wait up to an hour until they are shown to the end-user.
    async def setup_hook(self):
        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)


intents = discord.Intents.default()
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


client.run(os.environ['TOKEN'], log_handler=None)
