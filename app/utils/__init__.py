"""
Utility modules for CRAEFTO automation system
"""

from .database import (
    SupabaseClient,
    get_database,
    init_database,
    close_database,
    DatabaseSession,
    with_database,
    handle_database_errors,
    DatabaseError,
    ConnectionError,
    QueryError
)

__all__ = [
    'SupabaseClient',
    'get_database',
    'init_database',
    'close_database',
    'DatabaseSession',
    'with_database',
    'handle_database_errors',
    'DatabaseError',
    'ConnectionError',
    'QueryError'
]

# Note: Additional methods available on SupabaseClient:
# - save_research()
# - get_pending_content()
# - mark_published()
# - track_performance()
# - get_top_performing()
