class DbQueryError(Exception):
    """Base exception for all db-query errors."""

    status_code: str = "DB_QUERY_ERROR"

    def __init__(self, message: str, query_id: str | None = None) -> None:
        super().__init__(message)
        self.query_id = query_id


class ReadOnlyViolationError(DbQueryError):
    """Query contains write operations (INSERT, UPDATE, DELETE, etc.)."""

    status_code = "READ_ONLY_VIOLATION"


class UnknownDatabaseError(DbQueryError):
    """Referenced database connection name is not configured."""

    status_code = "UNKNOWN_DATABASE"


class SQLError(DbQueryError):
    """SQL parsing or execution error."""

    status_code = "SQL_ERROR"


class EmptyQueryError(DbQueryError):
    """Empty SQL query."""

    status_code = "EMPTY_QUERY"


class ConfigurationError(DbQueryError):
    """Configuration error (missing env vars, invalid URL, etc.)."""

    status_code = "CONFIGURATION_ERROR"
