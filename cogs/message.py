import traceback

import discord
from discord.ext import commands
import datetime

from database.DB import DB
from utils.logger import logger
from utils.check_permission import check_permission
from models.model_utils import *


class Message(commands.Cog):
    """class for manage messages in a guild"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        """listener when send a message in a chat"""
        if message.author.bot:
            return

        guild = await Guilds.get(guild_id=message.guild.id)
        price = guild.price_messages
        await Profiles.update(user_id=message.author.id,
                              guild_id=message.guild.id,
                              set=[
                                  f"messages = messages + 1, coins = coins + {price}, day_messages = day_messages + 1"])

    # @commands.Cog.listener()
    # async def on_message_edit(self, before, after):
    #     """listener when edit message"""
    #
    #     await self.send_embed_about_change_message(before, after)

    # @commands.Cog.listener()
    # async def on_raw_message_delete(self, payload):
    #     """listener when delete a message"""
    #     print()
    #     guild = self.bot.get_guild(payload.guild_id)
    #     audits = guild.audit_logs(limit=10)
    #     # audit = await audits.get(extra__channel=payload.cached_message.channel)
    #     async for i in audits:
    #         print(i)
    #     await self.send_embed_about_change_message(payload.cached_message)

    # async def send_embed_about_change_message(self, old, new=None):
    #
    #     now_date = datetime.datetime.now()
    #
    #     if new:
    #         new_content = f'***New content***: {new.content}\n'
    #         action = 'edit'
    #     else:
    #         new_content = ''
    #         action = 'delete'
    #
    #     embed = discord.Embed(
    #         title=f'{old.author.name}#{old.author.discriminator} {action} message',
    #         description=
    #         f'***Name***: {old.author.mention}\n '
    #         f'***ID***: {old.author.id}\n'
    #         f'***Channel***: {old.channel.name}\n'
    #         f'***Content***: {old.content}\n'
    #         f'{new_content}'
    #         f'***Date create***: {(old.created_at + datetime.timedelta(hours=3)).strftime("%d.%m.%Y %H:%M")}\n'
    #         f'***Date change***: {now_date.strftime("%d.%m.%Y %H:%M")}\n'
    #         , color=discord.Colour.red()
    #     )
    #
    #     guild = await get_guild_from_db(old.guild)
    #     log_channel_id = guild.log_channel_id
    #
    #     if old.author.bot is False:
    #         logger.info(f'{old.guild}: {old.author} {action} message in {old.channel.name}')
    #
    #         if log_channel_id:
    #             await self.bot.get_channel(log_channel_id).send(embed=embed)

    @commands.command(aliases=['emb'])
    @commands.check(check_permission)
    async def embed(self, ctx, title, description='', color=0x000000, url_thumbnail=''):
        """command send embed in a chat"""

        color = int(color)

        emb = discord.Embed(
            title=title,
            description=description,
            color=discord.Colour(color)
        )
        emb.set_thumbnail(url=url_thumbnail)

        await ctx.send(embed=emb)
        logger.info(f'{ctx.guild} embed send in chat {ctx.channel}')

    @commands.command()
    @commands.check(check_permission)
    async def role(self, ctx, role_id=None):
        """command send list users with goal role"""

        if role_id:
            try:
                role_id = int(role_id)
                guild_role = ctx.guild.get_role(role_id)
                if guild_role:
                    emb = discord.Embed(
                        title=f'Users with roles {guild_role}',
                        description=f'All users = {len(guild_role.members)}',
                        color=discord.Colour(0x000000)
                    )
                    for member in guild_role.members:
                        emb.add_field(name=member.name, value=member.status.value)

                    await ctx.send(embed=emb)
                    logger.info(f'{ctx.guild}: list users with role {guild_role} send in chat {ctx.channel}')

                else:
                    await ctx.send(f'{ctx.author.mention}, input role_id {role_id} is not found')
            except ValueError:
                await ctx.send(f'{ctx.author.mention}, input role_id {role_id} is error')
        else:
            await ctx.send(f'{ctx.author.mention}, input role_id')

    # @commands.Cog.listener()
    # async def on_command_error(self, ctx, ex):
    #     """catch command error"""
    #
    #     # list_commands = [command.name for command in ctx.bot.commands]
    #     mention_user = ctx.author.mention
    #
    #     if isinstance(ex, commands.CheckFailure):
    #         # guild_roles_id = [role.id for role in ctx.guild.roles]
    #         # perm_roles_id = await DB.get_permissions(ctx.guild, ctx.command)
    #         #
    #         # list_permission = []
    #         # if perm_roles_id:
    #         #     for r_id in perm_roles_id:
    #         #         if r_id in guild_roles_id:
    #         #             list_permission.append(ctx.guild.get_role(r_id).name)
    #         #
    #         # only_admin = 'only administrator'
    #         # resp = f'{mention_user}, you have not permission for command {ctx.command}.' \
    #         #        f' List permission - {list_permission if list_permission != [] else only_admin}'
    #         # await ctx.send(resp, delete_after=10)
    #         await ctx.send('commands.CheckFailure', delete_after=10)
    #     else:
    #         # await ctx.send(f'{mention_user}, command is not found. List commands - {list_commands}', delete_after=10)
    #         traceback.print_tb(ex)
    #         print(ex)
    #         traceback.print_stack()
    #         await ctx.send(f'{mention_user}, {ex}', delete_after=100)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Message(bot))
