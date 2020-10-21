from typing import Iterable, TypeVar

T = TypeVar("T")


def flatten(list_of_list: Iterable[Iterable[T]]) -> Iterable[T]:
    return [item for sublist in list_of_list for item in sublist]
