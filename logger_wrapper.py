from functools import wraps
from typing import Callable, TypeVar, ParamSpec
from .logger import logger


P = ParamSpec("P")
R = TypeVar("R")


def logger_wrapper(func: Callable[P, R]) -> Callable[P, R]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        with logger.catch():
            return func(*args, **kwargs)

    return wrapper
