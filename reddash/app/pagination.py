import typing  # isort:skip


class Pagination(typing.List):
    """Pagination class for lists"""

    DEFAULT_PER_PAGE = 20

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.total = 0
        self.per_page = 0
        self.pages = 0
        self.page = 0

    def __repr__(self) -> str:
        return f"<Pagination page={self.page} of {self.pages}>"

    def has_prev(self) -> bool:
        return self.page > 1

    def has_next(self) -> bool:
        return self.page < self.pages

    @property
    def elements_numbers(self) -> typing.List[int]:
        return list(range(1, self.total + 1))

    @property
    def pages_numbers(self) -> typing.List[int]:
        return list(range(1, self.pages + 1))

    @classmethod
    def from_list(
        cls,
        items: typing.List[typing.Any],
        per_page: typing.Optional[typing.Union[int, str]] = None,
        page: typing.Optional[typing.Union[int, str]] = None,
    ) -> typing.Any:
        per_page = (
            cls.DEFAULT_PER_PAGE
            if per_page is None
            else (
                int(per_page)
                if isinstance(per_page, str) and per_page.isdigit() and 1 <= int(per_page) <= 100
                else cls.DEFAULT_PER_PAGE
            )
        )
        page = (
            1
            if page is None
            else (int(page) if isinstance(page, str) and page.isdigit() and int(page) >= 1 else 1)
        )
        total = len(items)
        pages = (total // per_page) + (total % per_page > 0)
        page = min(page, pages)
        start = (page - 1) * per_page
        end = start + per_page
        pagination = cls(items[start:end])
        pagination.total = total
        pagination.per_page = per_page
        pagination.pages = pages
        pagination.page = page
        return pagination
