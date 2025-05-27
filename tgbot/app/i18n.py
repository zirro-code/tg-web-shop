from typing import Any

from loguru import logger


def recursive_get(data: dict[Any, Any], key: str):
    # TODO: this is incorrectly typed function
    current_level = data
    for level in key.split("."):
        try:
            current_level = current_level[level]
        except (
            KeyError,
            TypeError,
        ):
            return level

    return current_level


def t(key: str, chat_id: int) -> str:
    # TODO: implement translation functionality, in_memory if needed
    lang: str = "RU"

    if lang == "RU":
        language_translation = RU
    elif lang == "EN":
        language_translation = EN
    else:
        logger.error(f"Unknown translation language, {lang}")
        language_translation = EN

    return recursive_get(language_translation, key)  # type: ignore


EN: dict[str, str | dict[str, Any]] = {}
RU: dict[str, str | dict[str, Any]] = {"start": "Привет!"}
