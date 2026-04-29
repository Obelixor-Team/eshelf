"""Category model for organizing books."""

from dataclasses import dataclass


@dataclass
class Category:
    """Represents a bookshelf category.

    Attributes:
        id (int): Unique identifier for the category.
        name (str): Name of the category.
    """

    id: int
    name: str
