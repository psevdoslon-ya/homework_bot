class SendMessageFailure(Exception):
    """Ошибка отправки сообщений."""

    pass


class GetApiStatusError(Exception):
    """Ошибка доступа к API."""

    pass


class HttpStatusOkError(Exception):
    """HTTP статус не равен 200."""

    pass
