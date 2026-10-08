"""Bridge utilitario para carga de datos resiliente con soporte de PostgreSQL 18 y fallback local."""

from typing import Any, Callable, Optional, TypeVar

T = TypeVar("T")


def load_with_db_fallback(
    db_loader: Callable[..., Optional[T]],
    fallback_loader: Callable[[], T],
    require_db: bool = False,
    min_items: Optional[int] = None,
    warn_message: Optional[str] = None,
) -> T:
    """Intenta cargar datos desde la base de datos y recurre al cargador de respaldo si es necesario."""
    try:
        data = db_loader(require_db=require_db)
        if data is not None:
            if min_items is None or len(data) >= min_items:  # type: ignore[arg-type]
                return data
    except Exception as exc:
        if require_db:
            raise
        if warn_message:
            print(f"[Aviso] {warn_message}: {exc}")

    return fallback_loader()
