import discord

from bot.settings import DEFAULT_PREFIX
from models.my_orm import MaybeAcquire, Table


async def get_prefix(bot, msg: discord.message.Message):
    if not msg.guild:
        return DEFAULT_PREFIX
    else:
        sql = f"""
        SELECT bot_prefix FROM guilds WHERE guild_id = {msg.guild.id}
        """
        async with MaybeAcquire(connection=None, pool=Table._pool) as con:
            data = await con.fetchrow(sql)
        # data = await DB.sql_fetch(sql, True)
        prefix = data.get('bot_prefix')
        return prefix