import asyncio
import difflib
import itertools
import typing as t
from datetime import datetime
import random
from typing import Tuple

import discord
from discord import Colour
from discord.abc import GuildChannel
from discord.ext.commands import Cog, Context, Bot
from discord.utils import escape_markdown
from enum import Enum
from deepdiff import DeepDiff

from models.models import *
from models.model_utils import *
from utils.icons import Icons


class Event(Enum):
    """
    Event names. This does not include every event (for example, raw
    events aren't here), but only events used in ModLog for now.
    """

    guild_channel_create = "guild_channel_create"
    guild_channel_delete = "guild_channel_delete"
    guild_channel_update = "guild_channel_update"
    guild_role_create = "guild_role_create"
    guild_role_delete = "guild_role_delete"
    guild_role_update = "guild_role_update"
    guild_update = "guild_update"

    member_join = "member_join"
    member_remove = "member_remove"
    member_ban = "member_ban"
    member_unban = "member_unban"
    member_update = "member_update"

    message_delete = "message_delete"
    message_edit = "message_edit"

    voice_state_update = "voice_state_update"


GUILD_CHANNEL = t.Union[discord.CategoryChannel, discord.TextChannel, discord.VoiceChannel]

CHANNEL_CHANGES_UNSUPPORTED = ("permissions",)
CHANNEL_CHANGES_SUPPRESSED = ("_overwrites", "position")
ROLE_CHANGES_UNSUPPORTED = ("colour", "permissions")
VOICE_STATE_ATTRIBUTES = {
    "channel.name": "Channel",
    "self_stream": "Streaming",
    "self_video": "Broadcasting",
}


class ModLog(Cog, name="ModLog"):
    """Logging for server events and staff actions."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self._ignored = {event: [] for event in Event}

        self._cached_deletes = []
        self._cached_edits = []

    def ignore(self, event: Event, *items: int) -> None:
        """Add event to ignored events to suppress log emission."""
        for item in items:
            if item not in self._ignored[event]:
                self._ignored[event].append(item)

    async def send_log_message(
            self,
            icon_url: t.Optional[str],
            colour: t.Union[discord.Colour, int],
            title: t.Optional[str],
            text: str,
            thumbnail: t.Optional[t.Union[str, discord.Asset]] = None,
            image: t.Optional[t.Union[str, discord.Asset]] = None,
            guild: discord.Guild = None,
            ping_everyone: bool = False,
            files: t.Optional[t.List[discord.File]] = None,
            content: t.Optional[str] = None,
            additional_embeds: t.Optional[t.List[discord.Embed]] = None,
            additional_embeds_msg: t.Optional[str] = None,
            timestamp_override: t.Optional[datetime.datetime] = None,
            footer: t.Optional[str] = None,
            field: t.Optional[t.Tuple[str, str]] = None,
    ) -> Context:
        """Generate log embed and send to logging channel."""
        # Обрезать строку прямо, чтобы избежать удаления новой строки
        embed = discord.Embed(
            description=text[:2045] + "..." if len(text) > 2048 else text
        )

        if title and icon_url:
            embed.set_author(name=title, icon_url=icon_url)

        embed.colour = colour
        embed.timestamp = timestamp_override or datetime.datetime.utcnow()

        if footer:
            embed.set_footer(text=footer)

        if field:
            embed.add_field(name=field[0], value=field[1], inline=False)

        if thumbnail:
            embed.set_thumbnail(url=thumbnail)

        if ping_everyone:
            if content:
                content = f"@everyone\n{content}"
            else:
                content = "@everyone"

        guild_from_cache = self.bot.cached_guilds.get(guild.id)
        channel_id = guild_from_cache.log_channel_id
        channel = self.bot.get_channel(channel_id)
        log_message = await channel.send(
            content=content,
            embed=embed,
            files=files,
            allowed_mentions=discord.AllowedMentions(everyone=True)
        )

        if additional_embeds:
            if additional_embeds_msg:
                await channel.send(additional_embeds_msg)
            for additional_embed in additional_embeds:
                await channel.send(embed=additional_embed)

        return await self.bot.get_context(log_message)

    @Cog.listener()
    async def on_guild_channel_create(self, channel: GUILD_CHANNEL) -> None:
        """Log channel create event to mod log."""

        if isinstance(channel, discord.CategoryChannel):
            title = "Category created"
            message = f"{channel.name} (`{channel.id}`)"
        elif isinstance(channel, discord.VoiceChannel):
            title = "Voice channel created"

            if channel.category:
                message = f"{channel.category}/{channel.name} (`{channel.id}`)"
            else:
                message = f"{channel.name} (`{channel.id}`)"
        else:
            title = "Text channel created"

            if channel.category:
                message = f"{channel.category}/{channel.name} (`{channel.id}`)"
            else:
                message = f"{channel.name} (`{channel.id}`)"
        await self.send_log_message(Icons.hash_green, discord.Colour.blurple(),
                                    title, message, guild=channel.guild)

    @Cog.listener()
    async def on_guild_channel_delete(self, channel: GUILD_CHANNEL) -> None:
        """Log channel delete event to mod log."""

        if isinstance(channel, discord.CategoryChannel):
            title = "Category deleted"
        elif isinstance(channel, discord.VoiceChannel):
            title = "Voice channel deleted"
        else:
            title = "Text channel deleted"

        if channel.category and not isinstance(channel, discord.CategoryChannel):
            message = f"{channel.category}/{channel.name} (`{channel.id}`)"
        else:
            message = f"{channel.name} (`{channel.id}`)"

        await self.send_log_message(
            Icons.hash_red, discord.Colour.blurple(),
            title, message, guild=channel.guild
        )

    @Cog.listener()
    async def on_guild_channel_update(self, before: GUILD_CHANNEL, after: GuildChannel) -> None:
        """Log channel update event to mod log."""

        if before.id in self._ignored[Event.guild_channel_update]:
            self._ignored[Event.guild_channel_update].remove(before.id)
            return

        diff = DeepDiff(before, after)
        changes = []
        done = []

        diff_values = diff.get("values_changed", {})
        diff_values.update(diff.get("type_changes", {}))

        for key, value in diff_values.items():
            if not key:
                continue

            key = key[5:]  # Delete "root." prefix

            if "[" in key:
                key = key.split("[", 1)[0]

            if "." in key:
                key = key.split(".", 1)[0]
            if key in done or key in CHANNEL_CHANGES_SUPPRESSED:
                continue

            if key in CHANNEL_CHANGES_UNSUPPORTED:
                changes.append(f"**{key.title()}** updated")
            else:
                new = value["new_value"]
                old = value["old_value"]
                changes.append(f"**{key.title()}:** `{old or 'None'}` **→** `{new or 'None'}`")

            done.append(key)

        if not changes:
            return

        message = ""

        for item in sorted(changes):
            message += f"--- {item}\n"

        if after.category:
            message = f"**{after.category}/#{after.name} (`{after.id}`)**\n{message}"
        else:
            message = f"**#{after.name}** (`{after.id}`)\n{message}"

        await self.send_log_message(
            Icons.hash_blurple, discord.Colour.blurple(),
            "Channel updated", message, guild=before.guild
        )

    @Cog.listener()
    async def on_guild_role_create(self, role: discord.Role) -> None:
        """Log role create event to mod log."""

        await self.send_log_message(
            Icons.crown_green, discord.Colour.blurple(),
            "Role created", f"`{role.id}`",
            guild=role.guild
        )

    @Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role) -> None:
        """Log role delete event to mod log."""

        await self.send_log_message(
            Icons.crown_red, discord.Colour.blurple(),
            "Role removed", f"{role.name} (`{role.id}`)",
            guild=role.guild
        )

    @Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role) -> None:
        """Log role update event to mod log."""

        diff = DeepDiff(before, after)
        changes = []
        done = []

        diff_values = diff.get("values_changed", {})
        diff_values.update(diff.get("type_changes", {}))

        for key, value in diff_values.items():
            if not key:
                continue

            key = key[5:]  # Delete "root." prefix

            if "[" in key:
                key = key.split("[", 1)[0]

            if "." in key:
                key = key.split(".", 1)[0]

            if key in done or key == "color":
                continue

            if key in ROLE_CHANGES_UNSUPPORTED:
                changes.append(f"**{key.title()}** updated")
            else:
                new = value["new_value"]
                old = value["old_value"]

                changes.append(f"**{key.title()}:** `{old}` **→** `{new}`")

            done.append(key)

        if not changes:
            return

        message = ""

        for item in sorted(changes):
            message += f"--- {item}\n"

        message = f"**{after.name}** (`{after.id}`)\n{message}"

        await self.send_log_message(
            Icons.crown_blurple, discord.Colour.blurple(),
            "Role updated", message,
            guild=before.guild
        )

    @Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild) -> None:
        """Log guild update event to mod log."""

        diff = DeepDiff(before, after)
        changes = []
        done = []

        diff_values = diff.get("values_changed", {})
        diff_values.update(diff.get("type_changes", {}))

        for key, value in diff_values.items():
            if not key:
                continue

            key = key[5:]  # Delete "root." prefix

            if "[" in key:
                key = key.split("[", 1)[0]

            if "." in key:
                key = key.split(".", 1)[0]

            if key in done:
                continue

            new = value["new_value"]
            old = value["old_value"]

            changes.append(f"**{key.title()}:** `{old}` **→** `{new}`")

            done.append(key)

        if not changes:
            return

        message = ""

        for item in sorted(changes):
            message += f"--- {item}\n"

        message = f"**{after.name}** (`{after.id}`)\n{message}"

        await self.send_log_message(
            Icons.guild_update, discord.Colour.blurple(),
            "Guild updated", message,
            thumbnail=after.icon_url_as(format="png"),
            guild=before
        )

    @Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, member: discord.Member) -> None:
        """Log ban event to user log."""

        if member.id in self._ignored[Event.member_ban]:
            self._ignored[Event.member_ban].remove(member.id)
            return

        await self.send_log_message(
            Icons.user_ban, discord.Colour.red(),
            "User banned", f"{member} (`{member.id}`)",
            thumbnail=member.avatar_url_as(static_format="png"),
            guild=guild
        )

    @Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """Log member join event to user log."""

        invites_from_db = await Invites.get_many(guild_id=member.guild.id)
        new_invites = [invite for invite in await member.guild.invites()]
        new_invites_ids = [inv.id for inv in new_invites]
        for old_inv in invites_from_db:
            if old_inv not in new_invites_ids:
                if old_inv.max_uses == 1:
                    inv = old_inv
                    await Invites.delete_(id=inv.id)
                    await Profiles.update(user_id=inv.user_id,
                                          guild_id=inv.guild_id,
                                          set=["invites = invites + 1"])
            for new_inv in new_invites:
                if old_inv.id == new_inv.id:
                    if old_inv.uses < new_inv.uses:
                        inv = new_inv
                        await Invites.update(id=inv.id,
                                             set=["uses = uses + 1"])
                        await Profiles.update(user_id=inv.inviter.id,
                                              guild_id=inv.guild.id,
                                              set=["invites = invites + 1"])
        try:
            inviter = inv.inviter
        except AttributeError:
            inviter = self.bot.get_user(inv.user_id)

        message = f'{member.mention}#{member.discriminator}(`{member.id}`)'
        message += f'\n created_at={member.created_at}'
        field = ('invited by', f'{inviter.mention}')
        await self.send_log_message(
            Icons.sign_in, discord.Colour.red(),
            "User joined", message,
            thumbnail=member.avatar_url_as(static_format="png"),
            guild=member.guild,
            field=field
        )

    @Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        """Log member leave event to user log."""

        if member.id in self._ignored[Event.member_remove]:
            self._ignored[Event.member_remove].remove(member.id)
            return

        await self.send_log_message(
            Icons.sign_out, Colour.red(),
            "User left", f"{escape_markdown(str(member))} (`{member.id}`)",
            thumbnail=member.avatar_url_as(static_format="png"),
            guild=member.guild
        )

    @Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, member: discord.User) -> None:
        """Log member unban event to mod log."""

        if member.id in self._ignored[Event.member_unban]:
            self._ignored[Event.member_unban].remove(member.id)
            return

        member_str = escape_markdown(str(member))
        await self.send_log_message(
            Icons.user_unban, Colour.blurple(),
            "User unbanned", f"{member_str} (`{member.id}`)",
            thumbnail=member.avatar_url_as(static_format="png"),
            guild=guild
        )

    @staticmethod
    def get_role_diff(before: t.List[discord.Role], after: t.List[discord.Role]) -> t.List[str]:
        """Return a list of strings describing the roles added and removed."""
        changes = []
        before_roles = set(before)
        after_roles = set(after)

        for role in (before_roles - after_roles):
            changes.append(f"**Role removed:** {role.name} (`{role.id}`)")

        for role in (after_roles - before_roles):
            changes.append(f"**Role added:** {role.name} (`{role.id}`)")

        return changes

    @Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        """Log member update event to user log."""

        if before.id in self._ignored[Event.member_update]:
            self._ignored[Event.member_update].remove(before.id)
            return

        changes = self.get_role_diff(before.roles, after.roles)

        diff = DeepDiff(before, after, exclude_regex_paths=r".*\[.*")

        diff_values = {**diff.get("values_changed", {}), **diff.get("type_changes", {})}

        for attr, value in diff_values.items():
            if not attr:
                continue

            attr = attr[5:]  # Del "root." prefix.
            attr = attr.replace("_", " ").replace(".", " ").capitalize()

            new = value.get("new_value")
            old = value.get("old_value")

            changes.append(f"**{attr}:** `{old}` **→** `{new}`")

        if not changes:
            return

        message = ""

        for item in sorted(changes):
            message += f"--- {item}\n"

        member_str = escape_markdown(str(after))
        message = f"**{member_str}** (`{after.id}`)\n{message}"

        await self.send_log_message(
            icon_url=Icons.user_update,
            colour=Colour.blurple(),
            title="Member updated",
            text=message,
            thumbnail=after.avatar_url_as(static_format="png"),
            guild=before.guild
        )

    @Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        """Log message delete event to message change log."""
        channel = message.channel
        author = message.author

        # Игнорить ЛС
        if not message.guild:
            return

        self._cached_deletes.append(message.id)

        if message.id in self._ignored[Event.message_delete]:
            self._ignored[Event.message_delete].remove(message.id)
            return

        # игнорить ботов
        if author.bot:
            return

        author_str = author.mention
        if channel.category:
            response = (
                f"**Author:** {author_str} (`{author.id}`)\n"
                f"**Channel:** {channel.category}/#{channel.name} (`{channel.id}`)\n"
                f"**Message ID:** `{message.id}`\n"
                "\n"
            )
        else:
            response = (
                f"**Author:** {author_str} (`{author.id}`)\n"
                f"**Channel:** #{channel.name} (`{channel.id}`)\n"
                f"**Message ID:** `{message.id}`\n"
                "\n"
            )

        if message.attachments:
            # Добавить метаданные сообщения с количеством вложений
            response = f"**Attachments:** {len(message.attachments)}\n" + response

        # Сократить сообщение
        content = message.clean_content
        remaining_chars = 2040 - len(response)

        if len(content) > remaining_chars:
            botlog_url = await self.upload_log(messages=[message], actor_id=message.author.id)
            ending = f"\n\nMessage truncated, [full message here]({botlog_url})."
            truncation_point = remaining_chars - len(ending)
            content = f"{content[:truncation_point]}...{ending}"

        response += f"{content}"

        await self.send_log_message(
            Icons.message_delete, Colour.dark_green(),
            "Message deleted",
            response,
            guild=message.guild
        )

    @Cog.listener()
    async def on_raw_message_delete(self, event: discord.RawMessageDeleteEvent) -> None:
        """Log raw message delete event to message change log."""

        await asyncio.sleep(1)  # Подождите здесь на случай, если будет запущено обычное событие

        if event.message_id in self._cached_deletes:
            # Он был в кеше, и было запущено обычное событие
            self._cached_deletes.remove(event.message_id)
            return

        if event.message_id in self._ignored[Event.message_delete]:
            self._ignored[Event.message_delete].remove(event.message_id)
            return

        channel = self.bot.get_channel(event.channel_id)

        if channel.category:
            response = (
                f"**Channel:** {channel.category}/#{channel.name} (`{channel.id}`)\n"
                f"**Message ID:** `{event.message_id}`\n"
                "\n"
                "This message was not cached, so the message content cannot be displayed."
            )
        else:
            response = (
                f"**Channel:** #{channel.name} (`{channel.id}`)\n"
                f"**Message ID:** `{event.message_id}`\n"
                "\n"
                "This message was not cached, so the message content cannot be displayed."
            )

        guild = self.bot.get_guild(event.guild_id)

        await self.send_log_message(
            Icons.message_delete, Colour.gold(),
            "Message deleted",
            response,
            guild=guild
        )

    @Cog.listener()
    async def on_message_edit(self, msg_before: discord.Message, msg_after: discord.Message) -> None:
        """Log message edit event to message change log."""
        if not msg_before.guild or msg_before.author.bot:
            return

        self._cached_edits.append(msg_before.id)

        if msg_before.content == msg_after.content:
            return

        author = msg_before.author
        author_str = msg_before.author.mention

        channel = msg_before.channel
        channel_name = f"{channel.category}/{channel.mention}" if channel.category else f"{channel.mention}"

        diff = difflib.ndiff(msg_before.clean_content.split(), msg_after.clean_content.split())
        diff_groups = tuple(
            (diff_type, tuple(s[2:] for s in diff_words))
            for diff_type, diff_words in itertools.groupby(diff, key=lambda s: s[0])
        )

        content_before: t.List[str] = []
        content_after: t.List[str] = []

        for index, (diff_type, words) in enumerate(diff_groups):
            sub = ' '.join(words)
            if diff_type == '-':
                content_before.append(f"[{sub}](http://o.hi)")
            elif diff_type == '+':
                content_after.append(f"[{sub}](http://o.hi)")
            elif diff_type == ' ':
                if len(words) > 2:
                    sub = (
                        f"{words[0] if index > 0 else ''}"
                        " ... "
                        f"{words[-1] if index < len(diff_groups) - 1 else ''}"
                    )
                content_before.append(sub)
                content_after.append(sub)

        response = (
            f"**Author:** {author_str} (`{author.id}`)\n"
            f"**Channel:** {channel_name} (`{channel.id}`)\n"
            f"**Message ID:** `{msg_before.id}`\n"
            "\n"
            f"**Before**:\n{' '.join(content_before)}\n"
            f"**After**:\n{' '.join(content_after)}\n"
            "\n"
            f"[Jump to message]({msg_after.jump_url})"
        )

        if msg_before.edited_at:
            # Message was previously edited
            timestamp = msg_before.edited_at
            delta = msg_after.edited_at - msg_before.edited_at
            footer = f"Last edited {delta} ago"
        else:
            # Message was not previously edited
            timestamp = msg_before.created_at
            footer = None

        await self.send_log_message(
            Icons.message_edit, Colour.blurple(), "Message edited", response,
            guild=msg_before.guild, timestamp_override=timestamp, footer=footer
        )

    @Cog.listener()
    async def on_raw_message_edit(self, event: discord.RawMessageUpdateEvent) -> None:
        """Log raw message edit event to message change log."""
        try:
            channel = self.bot.get_channel(int(event.data["channel_id"]))
            message = await channel.fetch_message(event.message_id)
        except discord.NotFound:
            return

        if not message.guild or message.author.bot:
            return

        await asyncio.sleep(1)

        if event.message_id in self._cached_edits:
            # сообщение есть в кэше и было запущенно обычное событие, удалить из кэша
            self._cached_edits.remove(event.message_id)
            return

        author = message.author
        channel = message.channel
        channel_name = f"{channel.category}/#{channel.name}" if channel.category else f"#{channel.name}"

        before_response = (
            f"**Author:** {author} (`{author.id}`)\n"
            f"**Channel:** {channel_name} (`{channel.id}`)\n"
            f"**Message ID:** `{message.id}`\n"
            "\n"
            "This message was not cached, so the message content cannot be displayed."
        )

        after_response = (
            f"**Author:** {author} (`{author.id}`)\n"
            f"**Channel:** {channel_name} (`{channel.id}`)\n"
            f"**Message ID:** `{message.id}`\n"
            "\n"
            f"{message.clean_content}"
        )
        await self.send_log_message(
            Icons.message_edit, Colour.blurple(), "Message edited (Before)",
            before_response, guild=message.guild
        )

        await self.send_log_message(
            Icons.message_edit, Colour.blurple(), "Message edited (After)",
            after_response, guild=message.guild
        )

    @Cog.listener()
    async def on_voice_state_update(
            self,
            member: discord.Member,
            before: discord.VoiceState,
            after: discord.VoiceState
    ) -> None:
        """Log member voice state changes to the voice log channel."""

        if member.id in self._ignored[Event.voice_state_update]:
            self._ignored[Event.voice_state_update].remove(member.id)
            return

        # Исключить все атрибуты канала, кроме имени.
        diff = DeepDiff(
            before,
            after,
            exclude_paths=("root.session_id", "root.afk"),
            exclude_regex_paths=r"root\.channel\.(?!name)",
        )

        diff_values = {**diff.get("values_changed", {}), **diff.get("type_changes", {})}

        icon = Icons.voice_state_blue
        colour = Colour.blurple()
        changes = []

        for attr, values in diff_values.items():
            if not attr:
                continue

            old = values["old_value"]
            new = values["new_value"]

            attr = attr[5:]  # Remove "root." prefix.
            attr = VOICE_STATE_ATTRIBUTES.get(attr, attr.replace("_", " ").capitalize())

            changes.append(f"**{attr}:** `{old}` **→** `{new}`")

            # Установите значок и цвет встраивания в зависимости от того, какой атрибут был изменен.
            if any(name in attr for name in ("Channel", "deaf", "mute")):
                if new is None or new is True:
                    # Left a channel or was muted/deafened.
                    icon = Icons.voice_state_red
                    colour = Colour.gold()
                elif old is None or old is True:
                    # Joined a channel or was unmuted/undeafened.
                    icon = Icons.voice_state_green
                    colour = Colour.gold()

        if not changes:
            return

        member_str = escape_markdown(str(member))
        message = "\n".join(f"*** {item}" for item in sorted(changes))
        message = f"**{member_str}** (`{member.id}`)\n{message}"

        await self.send_log_message(
            icon_url=icon,
            colour=colour,
            title="Voice state updated",
            text=message,
            thumbnail=member.avatar_url_as(static_format="png"),
            guild=member.guild
        )


def setup(bot: Bot) -> None:
    bot.add_cog(ModLog(bot))
