"""结构化日志：所有 service/controller/task 只准调用 log_event。"""
import json
import logging
import sys

from app.constants.log_templates import LOG_TEMPLATES

LOGGER_NAME = "texforge"

logger = logging.getLogger(LOGGER_NAME)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def log_event(template_key: str, **fields) -> None:
    template = LOG_TEMPLATES.get(template_key)
    if template is None:
        template = template_key
    try:
        rendered = template.format(**fields)
    except (KeyError, IndexError):
        rendered = template
    logger.info(json.dumps({"event": template_key, "message": rendered, **fields}, ensure_ascii=False, default=str))
