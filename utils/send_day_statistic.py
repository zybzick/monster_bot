import asyncio
import datetime

from cogs.statistic import get_embed_day_statistic


async def send_day_statistic(bot):
    """loop send day statistic in trophy channel"""

    await bot.wait_until_ready()
    while not bot.is_closed():
        now = datetime.datetime.today().time()
        start = datetime.time(12, 0, 0, 0)
        end = datetime.time(13, 0, 0, 0)
        for guild in bot.guilds:
            channel = await DB.get_info_about_guilds(guild)
            channel = channel['trophy_channel_id']
            if channel:
                if start < now < end:
                    emb = await get_embed_day_statistic(bot, guild)
                    await bot.get_channel(channel).send(embed=emb)
                    await DB.restart_day_statistic(guild)

        await asyncio.sleep(60)
