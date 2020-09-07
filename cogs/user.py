import datetime
import random
import discord

from discord.ext import commands
from discord.utils import escape_markdown

from utils.logger import logger
from utils.check_permission import check_permission
from models.model_utils import *


class User(commands.Cog):
    """class for manage user"""

    def __init__(self, bot):
        self.bot = bot

    # async def action_for_join_remove(self, member, action):
    #
    #     emb = await self.get_embed_info_user(member, f'{action} in {member.guild}')
    #
    #     log_channel_id = await DB.get_info_about_guilds(member.guild)
    #     log_channel_id = log_channel_id['log_channel_id']
    #
    #     if log_channel_id:
    #         await self.bot.get_channel(log_channel_id).send(embed=emb)
    #
    #     words = await DB.get_user_count_names(member.guild)
    #     user_count_channel_id = await DB.get_info_about_guilds(member.guild)
    #     user_count_channel_id = user_count_channel_id['user_count_channel_id']
    #
    #     if user_count_channel_id:
    #         name = random.choice(words) if words else ''
    #         await self.bot.get_channel(user_count_channel_id).edit(name=f'{name}: {member.guild.member_count}')

    async def get_embed_info_user(self, member: discord.Member) -> discord.Embed:
        color_embed = discord.Colour.gold()
        profile_user = await Profiles.get(user_id=member.id)
        roles = ','.join(rol.name for rol in member.roles if str(rol.name) != '@everyone')
        text = (
            f"**Name**: {member.mention} \n"
            f"**Display name**: {member.display_name} \n"
            f"**Status**: `{member.status.value}` \n"
            f"**ID**: `{member.id}` \n"
            f"**Join in guild**: {str(profile_user.joined_at)[0:-10]} \n"
            f"**Create account**:  {str(member.created_at)[0:-10]} \n\n"
            f"**coins**: {profile_user.coins} \n"
            f"**minutes**: {profile_user.minutes} (today: {profile_user.day_minutes})\n"
            f"**level**: {profile_user.level} \n"
            f"**Roles**:  {roles} \n"
            f"**Joins**:  {profile_user.joins}``\n"
            f"**Invites**: {profile_user.invites} "
        )

        embed = discord.Embed(
            title=f'{member.name}#{member.discriminator}',
            description=text, color=color_embed
        )
        embed.set_footer(text=member.guild)

        return embed

    async def refresh_user_count_channel(self, guild: discord.Guild) -> None:
        words = await UserCountNames.get_many(guild_id=guild.id)
        words = [w.name for w in words]
        user_count_channel_id = self.bot.cached_guilds.get(guild.id).user_count_channel_id
        if user_count_channel_id:
            name = random.choice(words) if words else ''
            await self.bot.get_channel(user_count_channel_id).edit(name=f'{name}: {guild.member_count}')

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        if before.roles != after.roles:
            before_roles_ids = [r.id for r in before.roles]
            after_roles_ids = [r.id for r in after.roles]
            if len(after_roles_ids) > len(before_roles_ids):
                # if role war added
                new_role_id = list(set(after_roles_ids) - set(before_roles_ids))[0]
                new_role = next(rol for rol in after.roles if rol.id == new_role_id)
                await UserRoles.insert(user_id=after.id, guild_id=after.guild.id, role_id=new_role.id)
            else:
                # if role war deleted
                remove_role_id = list(set(before_roles_ids) - set(after_roles_ids))[0]
                rem_role = next(rol for rol in before.roles if rol.id == remove_role_id)
                await UserRoles.delete_(user_id=after.id, guild_id=after.guild.id, role_id=rem_role.id)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """Listener when user join in a guild"""

        await add_user_in_db(member, member.guild)

        guild_from_db = await Guilds.get(guild_id=member.guild.id)
        role_saver = guild_from_db.role_saver
        if role_saver:
            user_roles = await UserRoles.get_many(guild_id=member.guild.id, user_id=member.id)
            if user_roles:
                for rol in user_roles:
                    role = discord.utils.get(member.guild.roles, id=rol.role_id)
                    if role.name == '@everyone':
                        continue
                    else:
                        await member.add_roles(role)

        await Profiles.update(user_id=member.id,
                              guild_id=member.guild.id,
                              set=["joins = joins + 1"])
        await Guilds.update(guild_id=member.guild.id,
                            set=["day_joins = day_joins + 1"])

        await self.refresh_user_count_channel(member.guild)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Listener when user remove in a guild"""
        await self.refresh_user_count_channel(member.guild)
        logger.info(f'{member.guild}: user {member} remove from guild')

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        """Listener when user create invite in a guild"""
        await add_invite_in_db(invite)
        logger.info(f'{invite.guild}: user {invite.inviter} create invite')

    @commands.command(aliases=['i'])
    @commands.check(check_permission)
    async def info(self, ctx, member: discord.Member = None):
        """command send in chat info about user"""

        user = ctx.author if member is None else member

        emb = await self.get_embed_info_user(user)
        emb.set_image(url=user.avatar_url)

        await ctx.send(embed=emb)

    @commands.Cog.listener()
    async def on_voice_state_update(
            self, member: discord.Member,
            after: discord.VoiceState,
            before: discord.VoiceState
    ) -> None:
        """listener when change user voice status"""

        channel_before = 'Null' if before.channel is None else before.channel.id
        user_profile = await Profiles.get(user_id=member.id, guild_id=member.guild.id)
        last_channel = user_profile.channel_id
        old_time = user_profile.change_voice_status

        new_time = datetime.datetime.now()
        if not last_channel:
            await Profiles.update(user_id=member.id, guild_id=member.guild.id,
                                  set=[f"channel_id = {channel_before}",
                                       f"change_voice_status = '{new_time}'"])

        if last_channel and not before.afk and not after.afk:
            delta_time = new_time - old_time
            minutes = round(delta_time.seconds / 60)
            if 1 <= minutes <= 180:
                await Profiles.update(user_id=member.id, guild_id=member.guild.id,
                                      set=[f"channel_id = {channel_before}",
                                           f"change_voice_status = '{new_time}'",
                                           f"minutes = minutes + {minutes}",
                                           f"coins = coins + {minutes} * {user_profile.price_minutes}",
                                           f"day_minutes = day_minutes + 1"])
                logger.info(f'{member.guild}: user {member} seated {minutes} minutes in channel {before.channel}')
            elif minutes > 180:
                await Profiles.update(user_id=member.id, guild_id=member.guild.id,
                                      set=[f"channel_id = {channel_before}",
                                           f"change_voice_status = '{new_time}'",
                                           f"minutes = minutes + {minutes}",
                                           f"coins = coins + {180} * {user_profile.price_minutes}",
                                           f"day_minutes = day_minutes + 1"])
                logger.info(f'{member.guild}: user {member} seated over 180 minutes in channel {before.channel}')
            else:
                await Profiles.update(user_id=member.id, guild_id=member.guild.id,
                                      set=[f"channel_id = {channel_before}",
                                           f"change_voice_status = '{new_time}'"])
                logger.info(f'{member.guild}: {member} seated less than one a minutes in channel {before.channel}')
        else:
            logger.info(f'{member.guild}: user {member} connect in channel {before.channel}')


def setup(bot: commands.Bot) -> None:
    bot.add_cog(User(bot))
