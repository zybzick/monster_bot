import asyncio
from bot.settings import POSTGRES_USER, POSTGRES_PASS, POSTGRES_HOST, POSTGRES_DB
from bot.bot import MyBot
from models.my_orm import Table


def main():
    """loop run bot with pool postgres"""

    loop = asyncio.get_event_loop()
    bot = MyBot()

    # bot.pool = loop.run_until_complete(DB.create_pool(
    bot.pool = loop.run_until_complete(Table().create_pool(
        user=POSTGRES_USER,
        password=POSTGRES_PASS,
        database=POSTGRES_DB,
        host=POSTGRES_HOST
    ))
    # bot.db_manager = DB()
    bot.run()


if __name__ == '__main__':
    main()
