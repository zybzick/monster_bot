import asyncio
import datetime
import decimal
import inspect
import pydoc
from collections import OrderedDict
import asyncpg
import bot.settings


class SchemaError(Exception):
    pass


class SQLType:
    python = None

    def to_dict(self):
        o = self.__dict__.copy()
        cls = self.__class__
        o['__meta__'] = cls.__module__ + '.' + cls.__qualname__
        return o

    @classmethod
    def from_dict(cls, data):
        meta = data.pop('__meta__')
        given = cls.__module__ + '.' + cls.__qualname__
        if given != meta:
            cls = pydoc.locate(meta)
            if cls is None:
                raise RuntimeError(f'Could not locate "{meta}".')

        self = cls.__new__(cls)
        self.__dict__.update(data)
        return self

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self.__eq__(other)

    def to_sql(self):
        raise NotImplementedError()

    # def is_real_type(self):
    #     return True


class Binary(SQLType):
    python = bytes

    def to_sql(self):
        return 'BYTEA'


class Boolean(SQLType):
    python = bool

    def to_sql(self):
        return 'BOOLEAN'


class Date(SQLType):
    python = datetime.date

    def to_sql(self):
        return 'DATE'


class Datetime(SQLType):
    python = datetime.datetime

    def __init__(self, *, timezone=False):
        self.timezone = timezone

    def to_sql(self):
        if self.timezone:
            return 'TIMESTAMP WITH TIME ZONE'
        return 'TIMESTAMP'


class Double(SQLType):
    python = float

    def to_sql(self):
        return 'REAL'


class Float(SQLType):
    python = float

    def to_sql(self):
        return 'FLOAT'


class Integer(SQLType):
    python = int

    def __init__(self, *, big=False, small=False, auto_increment=False):
        self.big = big
        self.small = small
        self.auto_increment = auto_increment

        if big and small:
            raise SchemaError('Integer column type cannot be both big and small.')

    def to_sql(self):
        if self.auto_increment:
            if self.big:
                return 'BIGSERIAL'
            if self.small:
                return 'SMALLSERIAL'
            return 'SERIAL'
        if self.big:
            return 'BIGINT'
        if self.small:
            return 'SMALLINT'
        return 'INTEGER'

    def is_real_type(self):
        return not self.auto_increment


class Interval(SQLType):
    python = datetime.timedelta

    def __init__(self, field=None):
        if field:
            field = field.upper()
            if field not in ('YEAR', 'MONTH', 'DAY', 'HOUR', 'MINUTE', 'SECOND',
                             'YEAR TO MONTH', 'DAY TO HOUR', 'DAY TO MINUTE', 'DAY TO SECOND',
                             'HOUR TO MINUTE', 'HOUR TO SECOND', 'MINUTE TO SECOND'):
                raise SchemaError('invalid interval specified')
            self.field = field
        else:
            self.field = None

    def to_sql(self):
        if self.field:
            return 'INTERVAL ' + self.field
        return 'INTERVAL'


class Numeric(SQLType):
    python = decimal.Decimal

    def __init__(self, *, precision=None, scale=None):
        if precision is not None:
            if precision < 0 or precision > 1000:
                raise SchemaError('precision must be greater than 0 and below 1000')
            if scale is None:
                scale = 0

        self.precision = precision
        self.scale = scale

    def to_sql(self):
        if self.precision is not None:
            return f'NUMERIC({self.precision}, {self.scale})'
        return 'NUMERIC'


class String(SQLType):
    python = str

    def __init__(self, *, length=None, fixed=False):
        self.length = length
        self.fixed = fixed

        if fixed and length is None:
            raise SchemaError('Cannot have fixed string with no length')

    def to_sql(self):
        if self.length is None:
            return 'TEXT'
        if self.fixed:
            return f'CHAR({self.length})'
        return f'VARCHAR({self.length})'


class Time(SQLType):
    python = datetime.time

    def __init__(self, *, timezone=False):
        self.timezone = timezone

    def to_sql(self):
        if self.timezone:
            return 'TIME WITH TIME ZONE'
        return 'TIME'


class JSON(SQLType):
    python = None

    def to_sql(self):
        return 'JSONB'


class ForeignKey(SQLType):
    def __init__(self, table, column, *, sql_type=None, on_delete='CASCADE', on_update='NO ACTION'):
        if not table or not isinstance(table, str):
            raise SchemaError('missing table to reference (must be string)')

        valid_actions = (
            'NO ACTION',
            'RESTRICT',
            'CASCADE',
            'SET NULL',
            'SET DEFAULT',
        )

        on_delete = on_delete.upper()
        on_update = on_update.upper()

        if on_delete not in valid_actions:
            raise TypeError(f'on_delete must be one of {valid_actions}.')

        if on_update not in valid_actions:
            raise TypeError(f'on_update must be one of {valid_actions}.')

        self.table = table
        self.column = column
        self.on_update = on_update
        self.on_delete = on_delete

        if sql_type is None:
            sql_type = Integer

        if inspect.isclass(sql_type):
            sql_type = sql_type()

        if not isinstance(sql_type, SQLType):
            raise TypeError('Cannot have non-SQLType derived sql_type')

        if not sql_type.is_real_type():
            raise SchemaError('sql_type must be a "real" type')

        self.sql_type = sql_type.to_sql()

    def is_real_type(self):
        return False

    def to_sql(self):
        fmt = '{0.sql_type} REFERENCES {0.table} ({0.column})' \
              ' ON DELETE {0.on_delete} ON UPDATE {0.on_update}'
        return fmt.format(self)


class Array(SQLType):
    python = list

    def __init__(self, sql_type):
        if inspect.isclass(sql_type):
            sql_type = sql_type()

        if not isinstance(sql_type, SQLType):
            raise TypeError('Cannot have non-SQLType derived sql_type')

        if not sql_type.is_real_type():
            raise SchemaError('sql_type must be a "real" type')

        self.sql_type = sql_type.to_sql()

    def to_sql(self):
        return '{0.sql_type} ARRAY'.format(self)

    def is_real_type(self):
        return False


class Column:
    __slots__ = ('column_type', 'index', 'primary_key', 'nullable',
                 'default', 'unique', 'name', 'index_name')

    def __init__(self, column_type, *, index=False, primary_key=False,
                 nullable=True, unique=False, default=None, name=None):

        if inspect.isclass(column_type):
            column_type = column_type()

        if not isinstance(column_type, SQLType):
            raise TypeError('Cannot have a non-SQLType derived column_type')

        self.column_type = column_type
        self.index = index
        self.unique = unique
        self.primary_key = primary_key
        self.nullable = nullable
        self.default = default
        self.name = name
        self.index_name = None  # to be filled later

        if sum(map(bool, (unique, primary_key, default is not None))) > 1:
            raise SchemaError("'unique', 'primary_key', and 'default' are mutually exclusive.")

    @classmethod
    def from_dict(cls, data):
        index_name = data.pop('index_name', None)
        column_type = data.pop('column_type')
        column_type = SQLType.from_dict(column_type)
        self = cls(column_type=column_type, **data)
        self.index_name = index_name
        return self

    @property
    def _comparable_id(self):
        return '-'.join(f'{attr}:{getattr(self, attr)}' for attr in self.__slots__)

    def _to_dict(self):
        d = {
            attr: getattr(self, attr)
            for attr in self.__slots__
        }
        d['column_type'] = self.column_type.to_dict()
        return d

    def _qualifiers_dict(self):
        return {attr: getattr(self, attr) for attr in ('nullable', 'default')}

    def _is_rename(self, other):
        if self.name == other.name:
            return False

        return self.unique == other.unique and self.primary_key == other.primary_key

    def _create_table(self) -> str:
        builder = []
        builder.append(self.name)
        builder.append(self.column_type.to_sql())

        default = self.default
        if default is not None:
            builder.append('DEFAULT')
            if isinstance(default, str) and isinstance(self.column_type, String):
                builder.append(f"'{default}'")
            elif isinstance(default, bool):
                builder.append(str(default).upper())
            else:
                builder.append(f"({default})")
        elif self.unique:
            builder.append('UNIQUE')
        if not self.nullable:
            builder.append('NOT NULL')

        return ' '.join(builder)


class PrimaryKeyColumn(Column):
    """Shortcut for a SERIAL PRIMARY KEY column."""

    def __init__(self):
        super().__init__(Integer(auto_increment=True), primary_key=True)


class MaybeAcquire:

    def __init__(self, connection, *, pool):
        self.connection = connection
        self.pool = pool
        self._cleanup = False

    async def __aenter__(self):
        if self.connection is None:
            self._cleanup = True
            self._connection = c = await self.pool.acquire()
            return c
        return self.connection

    async def __aexit__(self, *args):
        if self._cleanup:
            await self.pool.release(self._connection)


class TableMeta(type):
    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        return OrderedDict()

    def __new__(cls, name, parents, dct, **kwargs):
        columns = []

        try:
            table_name = kwargs['table_name']
        except KeyError:
            table_name = name.lower()

        dct['__tablename__'] = table_name

        for elem, value in dct.items():
            if isinstance(value, Column):
                value.name = elem

                if value.index:
                    value.index_name = f'{table_name}_{value.name}_idx'

                columns.append(value)

        dct['columns'] = columns
        return super().__new__(cls, name, parents, dct)

    def __init__(self, name, parents, dct, **kwargs):
        super().__init__(name, parents, dct)


class Table(metaclass=TableMeta):
    @classmethod
    async def create_pool(cls, **kwargs):
        cls._pool = pool = await asyncpg.create_pool(**kwargs)
        return pool

    @classmethod
    async def create_table(cls, *, exists_ok=True, connection=None):
        statements = []
        builder = ['CREATE TABLE']

        if exists_ok:
            builder.append('IF NOT EXISTS')

        builder.append(cls.__tablename__)
        column_creations = []
        primary_keys = []
        for col in cls.columns:
            column_creations.append(col._create_table())
            if col.primary_key:
                primary_keys.append(col.name)

        column_creations.append(f'PRIMARY KEY ({", ".join(primary_keys)})')
        builder.append(f'({", ".join(column_creations)})')
        statements.append(' '.join(builder) + ';')

        # handle the index creations
        for column in cls.columns:
            if column.index:
                fmt = f'CREATE INDEX IF NOT EXISTS {column.index_name} ON {cls.__tablename__} ({column.name});'
                statements.append(fmt)

        sql = '\n'.join(statements)

        async with MaybeAcquire(connection, pool=cls._pool) as con:
            print(sql)
            await con.execute(sql)

    @classmethod
    async def drop_table(cls, *, connection=None):
        async with MaybeAcquire(connection, pool=cls._pool) as con:
            sql = f'DROP TABLE IF EXISTS {cls.__tablename__} CASCADE;'
            print(sql)
            await con.execute(sql)

    @classmethod
    async def insert(cls, connection=None, **kwargs):
        """Inserts an element to the table."""

        verified = {}
        for column in cls.columns:
            try:
                value = kwargs[column.name]
            except KeyError:
                continue

            # check = column.column_type.python
            if value is None and not column.nullable:
                raise TypeError(f'Cannot pass None to non-nullable column {column.name}.')
            # elif not check or not isinstance(value, check):
            #     fmt = f'column {column} expected {check}, received {value}'
            #     raise TypeError(fmt)

            verified[column.name] = value
        tab_rows = ', '.join(verified)
        tab_values = ', '.join(f'${str(i)}' for i, _ in enumerate(verified, 1))
        sql = f"INSERT INTO {cls.__tablename__} ({tab_rows}) VALUES ({tab_values});"

        async with MaybeAcquire(connection, pool=cls._pool) as con:
            try:
                # print(sql)
                await con.execute(sql, *verified.values())
                print(f"{verified} add in {cls.__tablename__}")
            except asyncpg.exceptions.UniqueViolationError:
                print(f'уже есть в бд {verified}')

    @classmethod
    async def get(cls, connection=None, **kwargs):
        """get an element to the table."""
        verified = {}
        joins_list = []
        for column in cls.columns:
            try:
                value = kwargs[column.name]
                if isinstance(column.column_type, ForeignKey):
                    foreign_key = column.column_type.column
                    table = column.column_type.table
                    join_string = f' LEFT JOIN {table} ON {cls.__tablename__}.{foreign_key} = {table}.{foreign_key}'
                    joins_list.append(join_string)
                    verified[f'{table}.{column.name}'] = value
                    continue
            except KeyError:
                continue
            verified[column.name] = value
        
        where = ' and '.join(f"{key}={value}" for key, value in verified.items())
        joins = ' '.join(joins_list)
        sql = f"SELECT * FROM {cls.__tablename__} {joins} where {where}"
        async with MaybeAcquire(connection, pool=cls._pool) as con:
            try:
                print(sql)
                fetch_result = await con.fetchrow(sql)
            except Exception as e:
                print(e)
        if fetch_result:
            obj = type(f'{cls.__tablename__}_obj', tuple(cls.mro()), dict(fetch_result))
            return obj()
        else:
            print('записи нет в бд')

    @classmethod
    async def get_many(cls, connection=None, ordered_by=None, limit=None, desc=False, **kwargs) -> list:
        """get an elements to the table."""

        sql = f"SELECT * FROM {cls.__tablename__}"

        if kwargs:
            par = []
            for key, value in kwargs.items():
                if key not in [i.name for i in cls.columns]:
                    raise Exception('такой строки нет у модели')
                if type(value) is str:
                    value = f"'{value}'"
                par.append(f"{key}={value}")

            params = ' and '.join(par)
            sql += f" where {params} "
        if ordered_by:
            arg = 'ASC' if not desc else 'DESC'
            sql += f" ORDER BY {ordered_by.name} {arg} "
        if limit:
            sql += f" LIMIT {limit} "

        async with MaybeAcquire(connection, pool=cls._pool) as con:
            print(sql)
            fetch_result = await con.fetch(sql)
        if fetch_result:
            objects = []
            for row in fetch_result:
                obj = type(f'{cls.__tablename__}_obj', tuple(cls.mro()), dict(row))
                objects.append(obj())
            return objects
        else:
            print('записи нет в бд')

    @classmethod
    async def update(cls, connection=None, **kwargs):
        """update an element to the table."""

        verified = {}
        for column in cls.columns:
            try:
                check = column.column_type.python
                if check is str:
                    value = f"'{kwargs[column.name]}'"
                else:
                    value = kwargs[column.name]
            except KeyError:
                continue
            verified[column.name] = value

        tab_name = cls.__tablename__
        sets = ', '.join(kwargs['set'])
        where = ' and '.join(f"{key}={value}" for key, value in verified.items())
        sql = f"UPDATE {tab_name} SET {sets} WHERE {where};"

        async with MaybeAcquire(connection, pool=cls._pool) as con:
            try:
                print(sql)
                await con.execute(sql)
            except asyncpg.exceptions.UniqueViolationError:
                print(f'UniqueViolationError')

    @classmethod
    async def delete_(cls, connection=None, **kwargs):
        """delete an element to the table."""
        verified = {}
        for column in cls.columns:
            try:
                if column.column_type.python is str:
                    value = f"'{kwargs[column.name]}'"
                else:
                    value = kwargs[column.name]
            except KeyError:
                continue
            verified[column.name] = value

        tab_name = cls.__tablename__
        where = ' and '.join(f"{key}={value}" for key, value in verified.items())
        sql = f"DELETE FROM {tab_name} WHERE {where};"

        async with MaybeAcquire(connection, pool=cls._pool) as con:
            try:
                await con.execute(sql)
                print(f"delete {where} from {tab_name}")
            except asyncpg.exceptions.UniqueViolationError:
                print(f'UniqueViolationError')

    @classmethod
    async def create_all_tables(cls):
        all_tables = cls.__subclasses__()
        for tab in all_tables:
            await tab.create_table()

    @classmethod
    async def delete_all_tables(cls):
        all_tables = cls.__subclasses__()
        for tab in all_tables:
            await tab.drop_table()

# async def main():
#     class Mem(Table):
#         id = Column(Integer(), primary_key=True)
#         pk = Column(Integer)
#         name = Column(String)
#         num = Column(Integer)
#
#         def __repr__(self):
#             return f"(obj id={self.id} name={self.name=})"
#
#     await Table().create_pool(user=bot.settings.POSTGRES_USER,
#                               password=bot.settings.POSTGRES_PASS,
#                               database=bot.settings.POSTGRES_DB,
#                               host=bot.settings.POSTGRES_HOST)
#
#     await Mem.drop()
#     await Mem.create_table()
#
#     for i in range(1, 33):
#         await Mem.insert(id=i, num=i+i*2, pk=i, name=f'{"n"*i}')
#     new_name = 'syka'
#     await Mem.update(id=22, pk=22, set=['num=num+1', f"name='{new_name}'"])
#
#     objs = await Mem.get_many(ordered_by=Mem.id)
#     print(objs)
#
#
# if __name__ == '__main__':
#     asyncio.run(main())
