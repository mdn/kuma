from __future__ import annotations

from typing import Generic, TypeVar

from django.conf import settings
from django.db.models import QuerySet
from django.http import HttpRequest
from django.middleware.csrf import get_token
from ninja import Field
from ninja.pagination import PageNumberPagination
from ninja.schema import Schema
from pydantic.generics import GenericModel

from kuma.settings.common import MAX_NON_SUBSCRIBED

ItemSchema = TypeVar("ItemSchema")


class PaginationInput(Schema):
    page: int = Field(1, gt=0)
    per_page: int = Field(settings.API_V1_PAGE_SIZE, ge=0, le=100)


class PaginatedMetadata(Schema):
    total: int
    page: int
    per_page: int
    max_non_subscribed: int


class PaginatedResponse(Schema, GenericModel, Generic[ItemSchema]):
    items: list[ItemSchema]
    metadata: PaginatedMetadata
    csrfmiddlewaretoken: str


class PaginatedData:
    items: QuerySet | list
    metadata: PaginatedMetadata
    csrfmiddlewaretoken: str

    def __init__(
        self,
        items: QuerySet | list,
        pagination: PaginationInput,
        csrfmiddlewaretoken: str,
    ):
        offset = (pagination.page - 1) * pagination.per_page
        self.items = items[offset : offset + pagination.per_page]
        self.metadata = PaginatedMetadata(
            total=items.count() if isinstance(items, QuerySet) else len(items),
            page=pagination.page,
            per_page=pagination.per_page,
            max_non_subscribed=MAX_NON_SUBSCRIBED.get(items.model.__name__, -1),
        )
        self.csrfmiddlewaretoken = csrfmiddlewaretoken


class PageNumberPaginationWithMeta(PageNumberPagination):
    Input = PaginationInput

    def paginate_queryset(
        self, items: QuerySet, request: HttpRequest, pagination: Input, **params
    ) -> PaginatedData:
        return PaginatedData(items, pagination, get_token(request))
