from .my_orm import *


class Users(Table, table_name='users'):
    id = Column(Integer(auto_increment=True), index=True, unique=True)
    user_id = Column(Integer(big=True), primary_key=True)
    created_at = Column(Datetime)


class Guilds(Table, table_name='guilds'):
    id = Column(Integer(auto_increment=True), index=True, unique=True)
    guild_id = Column(Integer(big=True), primary_key=True)
    created_at = Column(Datetime)
    day_joins = Column(Integer(big=True))
    day_removes = Column(Integer(big=True))
    bot_prefix = Column(String(length=20), default='!')
    log_channel_id = Column(Integer(big=True))
    trophy_channel_id = Column(Integer(big=True))
    user_count_channel_id = Column(Integer(big=True))
    price_minutes = Column(Integer(), default=2)
    price_messages = Column(Integer(), default=5)
    user_count = Column(Integer())
    role_saver = Column(Boolean(), default=True)


class Profiles(Table, table_name='user_profiles'):
    id = PrimaryKeyColumn()
    user_id = Column(ForeignKey('users', 'user_id', sql_type=Integer(big=True)))
    guild_id = Column(ForeignKey('guilds', 'guild_id', sql_type=Integer(big=True)))
    channel_id = Column(Integer(big=True))
    change_voice_status = Column(Datetime)
    coins = Column(Integer(), default=0)
    minutes = Column(Integer(), default=0)
    messages = Column(Integer(), default=0)
    level = Column(Integer(), default=1)
    joins = Column(Integer(), default=0)
    invites = Column(Integer(big=True), default=0)
    day_minutes = Column(Integer(), default=0)
    day_messages = Column(Integer(), default=0)
    joined_at = Column(Datetime)


class Channels(Table, table_name='channels'):
    id = Column(Integer(auto_increment=True), index=True, unique=True)
    channel_id = Column(Integer(big=True), primary_key=True)
    guild_id = Column(ForeignKey('guilds', 'guild_id', sql_type=Integer(big=True)))
    type_channel = Column(String(length=20))
    all_statistic = Column(Integer)
    day_statistic = Column(Integer)
    delete = Column(Datetime)
    name_after_delete = Column(String)


class Roles(Table, table_name='roles'):
    role_id = Column(Integer(big=True), primary_key=True)
    guild_id = Column(ForeignKey('guilds', 'guild_id', sql_type=Integer(big=True)))
    delete = Column(Datetime)
    name_after_delete = Column(String)


class UserRoles(Table, table_name='user_roles'):
    id = PrimaryKeyColumn()
    user_id = Column(ForeignKey('users', 'user_id', sql_type=Integer(big=True)))
    guild_id = Column(ForeignKey('guilds', 'guild_id', sql_type=Integer(big=True)))
    role_id = Column(ForeignKey('roles', 'role_id', sql_type=Integer(big=True)))


class Invites(Table, table_name='invites'):
    id = Column(String(length=20), primary_key=True)
    uses = Column(Integer)
    max_uses = Column(Integer)
    guild_id = Column(ForeignKey('guilds', 'guild_id', sql_type=Integer(big=True)))
    profile_id = Column(ForeignKey('user_profiles', 'id', sql_type=Integer(big=True)))
    user_id = Column(ForeignKey('users', 'user_id', sql_type=Integer(big=True)))


class Permissions(Table, table_name='permissions'):
    id = PrimaryKeyColumn()
    command = Column(String(length=100))
    guild_id = Column(ForeignKey('guilds', 'guild_id', sql_type=Integer(big=True)))
    role_id = Column(ForeignKey('roles', 'role_id', sql_type=Integer(big=True)))


class UserCountNames(Table, table_name='user_count_names'):
    id = PrimaryKeyColumn()
    guild_id = Column(ForeignKey('guilds', 'guild_id', sql_type=Integer(big=True)))
    name = Column(String(length=255))


async def create_all_tables():
    await Table().create_pool(user=bot.settings.POSTGRES_USER,
                              password=bot.settings.POSTGRES_PASS,
                              database=bot.settings.POSTGRES_DB,
                              host=bot.settings.POSTGRES_HOST)


if __name__ == '__main__':
    asyncio.run(create_all_tables())
