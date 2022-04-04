class NotForSendingError(Exception):
    pass


class NotSendingMessageError(NotForSendingError):
    def __init__(self):
        super().__init__(
            'Бот не смог отправить сообщение'
        )


class NotKeysError(NotForSendingError):
    def __init__(self):
        super().__init__(
            'Нет данных по ключам <homeworks> или <current_date>'
        )


class TypeListError(NotForSendingError):
    def __init__(self):
        super().__init__(
            'ДЗ приходят в виде списка'
        )


class UndocumentedStatusHomework(NotForSendingError):
    def __init__(self):
        super().__init__(
            'Недокументированный статус домашней работы'
        )


class ResponseStatusAPINot200(NotForSendingError):
    pass
