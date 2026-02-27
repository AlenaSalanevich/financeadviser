import logging
import sys


def setup_logging(level: str = "INFO") -> None:
    """Configure root logger with a readable format and silence noisy third-party libs."""
    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=fmt,
        datefmt=datefmt,
        stream=sys.stdout,
        force=True,
    )

    # Reduce noise from third-party libraries — only WARNING and above
    for noisy in ("httpx", "httpcore", "openai", "langchain", "urllib3", "multipart"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
