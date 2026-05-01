from abc import ABC


class InMemoryDB(ABC):
    """
    `InMemoryDB` interface.
    """

    def set(self, key: str, field: str, value: str) -> None:
        """
        Should insert a `field`-`value` pair to the record
        associated with `key`.
        If the `field` in the record already exists, replace the
        existing value with the specified `value`.
        If the record does not exist, create a new one.
        """
        pass

    def get(self, key: str, field: str) -> str | None:
        """
        Should return the value contained within `field` of the
        record associated with `key`.
        If the record or the `field` doesn't exist, should return
        `None`.
        """
        return None

    def delete(self, key: str, field: str) -> bool:
        """
        Should remove the `field` from the record associated with
        `key`.
        Returns `True` if the field was successfully deleted, and
        `False` if the `key` or the `field` do not exist in the
        database.
        """
        return False

    def scan(self, key: str) -> list[str]:
        """
        Should return a list of strings representing the fields of a
        record associated with `key`, each as "<field>(<value>)", with
        fields sorted lexicographically. Returns [] if the record
        does not exist.
        """
        return []

    def scan_by_prefix(self, key: str, prefix: str) -> list[str]:
        """
        Like scan, but only fields whose names start with `prefix`,
        sorted lexicographically. Returns [] if the record is missing
        or no fields match.
        """
        return []
