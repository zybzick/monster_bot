import discord
from discord import TextChannel
from discord.ext import commands
from .models import *
from typing import List


async def add_role_in_db(rol: discord.Role) -> None:
    await Roles.insert(
        role_id=rol.id,
        guild_id=rol.guild.id
    )


async def add_channel_in_db(channel: discord.channel) -> None:
    await Channels.insert(
        channel_id=channel.id,
        type_channel=channel.type.name,
        guild_id=channel.guild.id
    )


async def del_channel(channel: discord.channel) -> None:
    await Channels.delete_(
        channel_id=channel.id,
    )


async def add_user_in_db(mem: discord.Member, guild: discord.Guild) -> None:
    await Users.insert(user_id=mem.id,
                       created_at=mem.created_at)
    await Profiles.insert(user_id=mem.id,
                          guild_id=guild.id,)


async def add_invite_in_db(inv) -> None:
    await Invites.insert(
        id=inv.id,
        uses=inv.uses,
        max_uses=inv.max_uses,
        guild_id=inv.guild.id,
        user_id=inv.inviter.id,
    )


async def get_guild_from_db(guild: discord.Guild) -> Guilds:
    return await Guilds.get(guild_id=guild.id)


async def get_all_guild_from_db() -> List[Guilds]:
    return await Guilds.get_many()


async def get_permissions_from_db(ctx: commands.Context) -> List[Permissions]:
    return await Permissions.get_many(guild_id=ctx.guild.id, command=ctx.command.name)


async def get_user_roles(member: discord.Member) -> List[UserRoles]:
    return await UserRoles.get_many(guild_id=member.guild.id, user_id=member.id)


async def del_role(rol: discord.Role) -> None:
    await Roles.delete_(
        role_id=rol.id,
    )


async def guild_init(guild: discord.guild, bot) -> None:
    text_channels = [c for c in guild.channels if isinstance(c, TextChannel)]
    log_channels = [c for c in text_channels if 'log' in c.name]
    log_channel_id = log_channels[0].id if log_channels else text_channels[-1].id

    await Guilds.insert(guild_id=guild.id, user_count=guild.member_count, log_channel_id=log_channel_id)

    for rol in guild.roles:
        await add_role_in_db(rol)

    for channel in guild.channels:
        await add_channel_in_db(channel)

    for mem in guild.members:
        await add_user_in_db(mem, guild)

        for member_rol in mem.roles:
            await UserRoles.insert(user_id=mem.id, guild_id=guild.id, role_id=member_rol.id)

    for inv in await guild.invites():
        if inv.max_uses == 1:
            await inv.delete(reason='initial delete invite when max_uses == 1')
            continue
        await add_invite_in_db(inv)

    for command in bot.commands:
        await Permissions.insert(guild_id=guild.id,
                                 command=command.name)
