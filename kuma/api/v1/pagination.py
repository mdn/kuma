from __future__ import annotations

from typing import Generic, TypeVar

from django.conf import settings
from django.db.models import QuerySet
from django.http import HttpRequest
from django.middleware.csrf import get_token
from ninja import Field
from ninja.pagination import LimitOffsetPagination
from ninja.schema import Schema
from pydantic.generics import GenericModel

ItemSchema = TypeVar("ItemSchema")


class PaginationInput(Schema):
    page: int = Field(1, gt=0)
    per_page: int = Field(settings.API_V1_PAGE_SIZE, ge=0, le=100)


class LimitOffsetInput(Schema):
    limit: int = Field(20, gt=0)
    offset: int = Field(0, ge=1)


class PaginatedMetadata(Schema):
    total: int
    page: int
    per_page: int
    max_non_subscribed: int


class PaginatedResponse(Schema, GenericModel, Generic[ItemSchema]):
    items: list[ItemSchema]
    metadata: PaginatedMetadata
    csrfmiddlewaretoken: str


class LimitOffsetPaginatedData:
    items: QuerySet | list
    csrfmiddlewaretoken: str

    def __init__(self, items: QuerySet | list, csrfmiddlewaretoken: str):
        self.items = items
        self.csrfmiddlewaretoken = csrfmiddlewaretoken


class LimitOffsetPaginatedResponse(Schema, GenericModel, Generic[ItemSchema]):
    items: list[ItemSchema]
    csrfmiddlewaretoken: str


class LimitOffsetPaginationWithMeta(LimitOffsetPagination):
    def paginate_queryset(
        self, items: QuerySet, request: HttpRequest, **params
    ) -> LimitOffsetPaginatedData:
        paginated_items = super().paginate_queryset(items, request, **params)
        return LimitOffsetPaginatedData(
            paginated_items, csrfmiddlewaretoken=get_token(request)
        )
