"""Fachada transicional de compatibilidad hacia infrastructure/repositories/encuesta_repo.py."""

from backend.app.infrastructure.repositories.encuesta_repo import EncuestaRepository

__all__ = ["EncuestaRepository"]
