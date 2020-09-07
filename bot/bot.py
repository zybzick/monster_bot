import os
import discord
import sys
from discord.ext import commands

from bot.settings import DISCORD_BOT_TOKEN
from utils.get_prefix import get_prefix
from utils.logger import logger
from utils.send_day_statistic import send_day_statistic
from models.my_orm import Table
from models.model_utils import *


class MyBot(commands.Bot):
    """Manage bot"""

    def __init__(self):
        """initialize extensions in a bot"""

        super().__init__(command_prefix=get_prefix)

        cogs = [f'cogs.{i[0:-3]}' for i in os.listdir(path="./cogs") if not i.startswith('__')]
        for extension in cogs:
            try:
                self.load_extension(extension)
            except Exception as ex:
                logger.error(f'Failed to load extension {ex}.', file=sys.stderr)

        self.bg_task = self.loop.create_task(send_day_statistic(self))
        self.cached_guilds = {}

    async def on_ready(self):
        """listener when bot is ready"""

        game = discord.Game('SJW & BLM')
        await self.change_presence(status=discord.Status.online, activity=game)

        await Table.delete_all_tables()
        await Table.create_all_tables()

        for guild in self.guilds:
            await guild_init(guild, self)

        await self.refresh_cached_guilds()

        logger.info(f'{self.user} is ready on {len(self.guilds)} a guilds')

    async def refresh_cached_guilds(self):
        guild_list = await get_all_guild_from_db()
        self.cached_guilds = {guild.guild_id: guild for guild in guild_list}

    def run(self):
        """run bot with catch failed to load extension"""

        logger.info(f'run bot')
        try:
            super().run(DISCORD_BOT_TOKEN, reconnect=True)
        except Exception as ex:
            logger.warning(f'Failed to load extension {ex}.', file=sys.stderr)
