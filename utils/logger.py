import logging

logging.basicConfig(level=logging.INFO)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')
handler = logging.FileHandler(filename='debug.log', encoding='utf-8')
handler.setLevel(logging.INFO)
handler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(handler)

# loggers - корзина с логами
# handlers - обработчик куда складывать логи
# formatter - редактирование сообщения
# filters - фильтрация сообщений

# # Сообщение отладочное
# logging.debug( u'This is a debug message' )
# # Сообщение информационное
# logging.info( u'This is an info message' )
# # Сообщение предупреждение
# logging.warning( u'This is a warning' )
# # Сообщение ошибки
# logging.error( u'This is an error message' )
# # Сообщение критическое
# logging.critical( u'FATAL!!!' )
