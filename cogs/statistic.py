import asyncio
import datetime

import discord
from Cybernator import Paginator
from discord.ext import commands

from database.DB import DB
from utils.check_permission import check_permission

START = datetime.datetime.today().date()
END = START + datetime.timedelta(days=1)
OLD_START = START - datetime.timedelta(days=1)
OLD_END = END - datetime.timedelta(days=1)


class Statistic(commands.Cog):
    """Статистика сервер и его участников"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['s'])
    @commands.check(check_permission)
    async def stat(self, ctx):
        day = await self.day(ctx)
        invites = await self.top_invites(ctx)
        chat_users = await self.top_users(ctx, 'messages')
        voice_users = await self.top_users(ctx, 'minutes')
        chat_channels = await self.top_channels(ctx, 'text')
        voice_channels = await self.top_channels(ctx, 'voice')

        embeds = [day, invites, chat_users, voice_users, chat_channels, voice_channels]
        message = await ctx.send(embed=day)
        page = Paginator(self.bot, message, only=ctx.author, use_more=False, embeds=embeds)
        await page.start()

    async def day(self, ctx):
        emb = await get_embed_day_statistic(self.bot, ctx.guild)
        return emb

    async def top_invites(self, ctx):
        res = await DB.get_top_invites(ctx.guild)

        emb = discord.Embed(
            title=f'{ctx.guild}:rainbow_flag: Top invites',
            description='',
            color=discord.Colour.dark_gold(),
        )

        counter = 0
        for k, v in res.items():
            counter += 1
            emb.add_field(name=f'{counter}. {self.bot.get_user(v)}', value=f'{k}', inline=False)
        return emb

    @commands.command(aliases=['tc'])
    @commands.check(check_permission)
    async def top_coins(self, ctx):
        await self.top_users(ctx, 'coins')

    async def top_users(self, ctx, object):
        top_users = await DB.get_top_users(ctx.guild, object, 10)

        emb = discord.Embed(
            title=f'{ctx.guild}:rainbow_flag: Top users by {object}',
            description='',
            color=discord.Colour.dark_gold(),
        )

        for i, member in enumerate(top_users):
            emb.add_field(name=f'{i+1}. {self.bot.get_user(member)}', value=f'{top_users[member]}', inline=False)

        # await ctx.send(embed=emb)
        return emb

    async def top_channels(self, ctx, type_channel):
        top_channels = await DB.get_top_channels(ctx.guild, type_channel, 10)

        emb = discord.Embed(
            title=f'{ctx.guild}:rainbow_flag: Top {type_channel} channels:keyboard:',
            description='',
            color=discord.Colour.dark_gold(),
        )

        for i, channel in enumerate(top_channels):
            emb.add_field(name=f'{i+1}. {self.bot.get_channel(channel)}', value=f'{top_channels[channel]}', inline=False)

        await ctx.send(embed=emb)


async def get_embed_day_statistic(bot, guild):
    today = datetime.datetime.today().date()
    join_remove_day_guild = await DB.get_join_remove_day_guild(guild)

    max_new_user_minutes = await DB.get_top_new_users(guild, 'day_minutes')
    if max_new_user_minutes:
        row_max_new_user_minutes = f"""***Best new user in voices***: ``{bot.get_user(max_new_user_minutes[0])}`` - ``{(max_new_user_minutes[1])}`` minutes\n"""
    else:
        row_max_new_user_minutes = ''

    max_new_user_messages = await DB.get_top_new_users(guild, 'day_messages')
    if max_new_user_messages:
        row_max_new_user_messages = f"""***Best new user in chats***: ``{bot.get_user(max_new_user_messages[0])}`` - ``{(max_new_user_messages[1])}`` messages\n"""
    else:
        row_max_new_user_messages = ''

    top_text_channel_day = await DB.get_top_channel_day(guild, 'text')

    if len(top_text_channel_day) >= 1:
        row_text_channel = f'***Top-3 text channel***:\n'
        name_last_channel = await DB.get_name_last_channel(list(top_text_channel_day.keys())[0])
        if name_last_channel:
            row_text_channel_1 = f'***1. ***: ``{name_last_channel}`` - ``{list(top_text_channel_day.values())[0]}``\n'
        else:
            row_text_channel_1 = f'***1. ***: ``{bot.get_channel(list(top_text_channel_day.keys())[0])}`` - ``{list(top_text_channel_day.values())[0]}``\n'
    else:
        row_text_channel = ''
        row_text_channel_1 = ''

    if len(top_text_channel_day) >= 2:
        name_last_channel = await DB.get_name_last_channel(list(top_text_channel_day.keys())[1])
        if name_last_channel:
            row_text_channel_2 = f'***1. ***: ``{name_last_channel}`` - ``{list(top_text_channel_day.values())[1]}``\n'
        else:
            row_text_channel_2 = f'***1. ***: ``{bot.get_channel(list(top_text_channel_day.keys())[1])}`` - ``{list(top_text_channel_day.values())[1]}``\n'
    else:
        row_text_channel_2 = ''

    if len(top_text_channel_day) >= 3:
        name_last_channel = await DB.get_name_last_channel(list(top_text_channel_day.keys())[2])
        if name_last_channel:
            row_text_channel_3 = f'***1. ***: ``{name_last_channel}`` - ``{list(top_text_channel_day.values())[2]}``\n'
        else:
            row_text_channel_3 = f'***1. ***: ``{bot.get_channel(list(top_text_channel_day.keys())[2])}`` - ``{list(top_text_channel_day.values())[2]}``\n'
    else:
        row_text_channel_3 = ''
    total_messages = 0
    for k, v in top_text_channel_day.items():
        total_messages = total_messages + v


    top_minutes_channel_day = await DB.get_top_channel_day(guild, 'voice')

    if len(top_minutes_channel_day) >= 1:
        row_voice_channel = f'***Top-3 voice channel***:\n'


        row_voice_channel_1 = f'***1. ***: ``{bot.get_channel(list(top_minutes_channel_day.keys())[0])}`` - ``{list(top_minutes_channel_day.values())[0]}``\n'
    else:
        row_voice_channel = ''
        row_voice_channel_1 = ''
    if len(top_minutes_channel_day) >= 2:
        row_voice_channel_2 = f'***2. ***: ``{bot.get_channel(list(top_minutes_channel_day.keys())[1])}`` - ``{list(top_minutes_channel_day.values())[1]}``\n'
    else:
        row_voice_channel_2 = ''

    if len(top_minutes_channel_day) >= 3:
        row_voice_channel_3 = f'***3. ***: ``{bot.get_channel(list(top_minutes_channel_day.keys())[2])}`` - ``{list(top_minutes_channel_day.values())[2]}``\n'
    else:
        row_voice_channel_3 = ''
    total_minutes = 0
    for k, v in top_minutes_channel_day.items():
        total_minutes = total_minutes + v



    top_users_in_voices = await DB.get_top_users( guild, 'day_minutes', 3)

    if len(top_users_in_voices) >= 1:
        row_voice_user = f'***Top-3 user in voice channel***:\n'
        row_voice_user_1 = f'***1. ***: ``{bot.get_user(list(top_users_in_voices.keys())[0])}`` - ``{list(top_users_in_voices.values())[0]}``\n'
    else:
        row_voice_user = ''
        row_voice_user_1 = ''
    if len(top_users_in_voices) >= 2:
        row_voice_user_2 = f'***2. ***: ``{bot.get_user(list(top_users_in_voices.keys())[1])}`` - ``{list(top_users_in_voices.values())[1]}``\n'
    else:
        row_voice_user_2 = ''
    if len(top_users_in_voices) >= 3:
        row_voice_user_3 = f'***3. ***: ``{bot.get_user(list(top_users_in_voices.keys())[2])}`` - ``{list(top_users_in_voices.values())[2]}``\n'
    else:
        row_voice_user_3 = ''



    top_users_in_chats = await DB.get_top_users( guild, 'day_messages', 3)

    if len(top_users_in_chats) >= 1:
        row_text_user = f'***Top-3 user in text channel***:\n'
        row_text_user_1 = f'***1. ***: ``{bot.get_user(list(top_users_in_chats.keys())[0])}`` - ``{list(top_users_in_chats.values())[0]}``\n'
    else:
        row_text_user = ''
        row_text_user_1 = ''
    if len(top_users_in_chats) >= 2:
        row_text_user_2 = f'***2. ***: ``{bot.get_user(list(top_users_in_chats.keys())[1])}`` - ``{list(top_users_in_chats.values())[1]}``\n'
    else:
        row_text_user_2 = ''
    if len(top_users_in_chats) >= 3:
        row_text_user_3 = f'***3. ***: ``{bot.get_user(list(top_users_in_chats.keys())[2])}`` - ``{list(top_users_in_chats.values())[2]}``\n'
    else:
        row_text_user_3 = ''

    embed = discord.Embed(
        title=f'{guild} :rainbow_flag: Summary day ({today.strftime("%d.%m.%Y")}):',
        description=
        f'***All users***: ``{guild.member_count}``\n'
        f'***Change all users***: + ``{join_remove_day_guild[0]}`` - ``{join_remove_day_guild[1]}`` = ``{join_remove_day_guild[0] - join_remove_day_guild[1]}``\n'
        f'{row_max_new_user_minutes}'
        f'{row_max_new_user_messages}'

        f'\n***Unique users in voices***: ``{len(top_users_in_voices)}``\n'
        f'***Total minutes in voices***: ``{total_minutes}``\n'
        f'{row_voice_channel}'
        f'{row_voice_channel_1}'
        f'{row_voice_channel_2}'
        f'{row_voice_channel_3}'

        f'{row_voice_user}'
        f'{row_voice_user_1}'
        f'{row_voice_user_2}'
        f'{row_voice_user_3}'

        f'\n***Unique users in chats***: ``{len(top_users_in_chats)}``\n'
        f'***Total messages in chats***: ``{total_messages}``\n'
        f'{row_text_channel}'
        f'{row_text_channel_1}'
        f'{row_text_channel_2}'
        f'{row_text_channel_3}'

        f'{row_text_user}'
        f'{row_text_user_1}'
        f'{row_text_user_2}'
        f'{row_text_user_3}'
        , color=discord.Colour.dark_gold()
    )
    return embed


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Statistic(bot))
