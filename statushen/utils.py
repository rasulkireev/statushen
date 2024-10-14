import structlog


def get_statushen_logger(name):
    """This will add a `statushen` prefix to logger for easy configuration."""

    return structlog.get_logger(f"statushen.{name}")
