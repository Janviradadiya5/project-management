import uuid
from datetime import datetime, timezone

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardResultsPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
    page_query_param = "page"

    def get_paginated_response(self, data):
        return Response(
            {
                "success": True,
                "message": "List fetched.",
                "data": data,
                "meta": {
                    "pagination": {
                        "page": self.page.number,
                        "page_size": self.get_page_size(self.request),
                        "total_items": self.page.paginator.count,
                        "total_pages": self.page.paginator.num_pages,
                        "has_next": self.page.has_next(),
                        "has_previous": self.page.has_previous(),
                    },
                    "request_id": str(uuid.uuid4()),
                    "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                },
            }
        )

    def get_paginated_response_schema(self, schema):
        return schema

