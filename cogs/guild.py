import typing as t

from discord.ext.commands import Cog, Context
import discord

from models.model_utils import *
from utils.check_permission import check_permission
from utils.logger import logger


class Guild(commands.Cog):
    """class for manage a guild"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        """listener when send a message in a chat"""
        await add_role_in_db(role)
        logger.info(f'{role.guild}: role {role} create')

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        """listener when send a message in a chat"""
        await del_role(role)
        logger.info(f'{role.guild}: role {role} delete')

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        """listener when send a message in a chat"""
        await add_channel_in_db(channel)
        logger.info(f'{channel.guild}: channel {channel} create')

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        """listener when send a message in a chat"""
        await del_channel(channel)
        logger.info(f'{channel.guild}: channel {channel} dalete')

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """listener when bot adds a new guild"""
        await guild_init(guild)
        logger.info(f'{self.bot.user} add in {guild}, is {len(self.bot.guilds)} a guild')

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        """listener when bot remove from a guild"""
        logger.info(f'{self.bot.user} remove from a guild {guild}, bot lost on {len(self.bot.guilds)} a guilds')

    @commands.command()
    @commands.check(check_permission)
    async def guild(self, ctx):
        """Command for send info about a user"""

        guild_from_db = await Guilds.get(guild_id=ctx.guild.id)

        emb = discord.Embed(
            title=f'{ctx.guild}: info',
            description=
            f"""***Users***: ``{ctx.guild.member_count}``\n"""
            f"""***Create guild***: ``{ctx.guild.created_at.strftime("%d %h %Y %H:%M:%S")}``\n"""
            f"""***bot_prefix***: ``{guild_from_db.bot_prefix}``\n\n"""

            f"""***log_channel_id***: ``{guild_from_db.log_channel_id}``\n"""
            f"""***trophy_channel_id***: ``{guild_from_db.trophy_channel_id}``\n"""
            f"""***user_count_channel_id***: ``{guild_from_db.user_count_channel_id}``\n"""
            f"""***price_minutes***: ``{guild_from_db.price_minutes}``\n"""
            f"""***price_messages***: ``{guild_from_db.price_minutes}``\n"""
            f"""***role_saver***: ``{guild_from_db.role_saver}``\n"""
            , color=discord.Colour.gold()
        )
        emb.set_footer(text=ctx.guild)
        emb.set_image(url=ctx.guild.icon_url)
        await ctx.send(embed=emb)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Guild(bot))

