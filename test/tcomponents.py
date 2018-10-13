from core.utils import ILogger


class DummyLogger(ILogger):
    def get_child(self, name: str) -> 'ILogger':
        return self

    def debug(self, message, *args, **kwargs):
        pass

    def info(self, message, *args, **kwargs):
        pass

    def warning(self, message, *args, **kwargs):
        pass

    def error(self, message, *args, **kwargs):
        pass

    def critical(self, message, *args, **kwargs):
        pass
