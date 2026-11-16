import json
import logging
import sys
from typing import Any, Dict


class PiiSanitizerFilter(logging.Filter):
    """Filtra y remueve atributos con información de identificación personal (PII)."""

    PII_KEYS = {
        "cedula",
        "nombre_apellido",
        "casa_apartamento",
        "avenida_calle",
        "telefono",
        "correo",
        "email",
    }

    def filter(self, record: logging.LogRecord) -> bool:
        # Si el log trae extras en un dict
        if hasattr(record, "extra") and isinstance(record.extra, dict):  # type: ignore[attr-defined]
            record.extra = self._sanitize(record.extra)  # type: ignore[attr-defined]

        # Sanitizar argumentos si son diccionarios
        if isinstance(record.args, dict):
            record.args = self._sanitize(record.args)
        elif isinstance(record.args, tuple):
            record.args = tuple(
                self._sanitize(arg) if isinstance(arg, dict) else arg
                for arg in record.args
            )

        return True

    def _sanitize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        sanitized: Dict[str, Any] = {}
        for k, v in data.items():
            if k.lower() in self.PII_KEYS:
                sanitized[k] = "[REDACTED_PII]"
            elif isinstance(v, dict):
                sanitized[k] = self._sanitize(v)
            else:
                sanitized[k] = v
        return sanitized


class StructuredJsonFormatter(logging.Formatter):
    """Formateador estructurado en formato JSON para observabilidad de producción."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Extra fields agregados en el log
        if hasattr(record, "extra") and isinstance(record.extra, dict):  # type: ignore[attr-defined]
            for k, v in record.extra.items():  # type: ignore[attr-defined]
                if k not in log_obj:
                    log_obj[k] = v

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj, ensure_ascii=False)


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    app_logger = logging.getLogger("alcaldia.pdul")
    app_logger.setLevel(level)

    # Evitar duplicar handlers si ya se configuró
    if not app_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        handler.addFilter(PiiSanitizerFilter())
        handler.setFormatter(StructuredJsonFormatter())
        app_logger.addHandler(handler)

    return app_logger


logger = setup_logging()
