from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="Fluctua NFTs Service API",
        default_version="v1",
        description="API to manage Fluctua NFTs",
        contact=openapi.Contact(email="info@fluctuarecords.com"),
        license=openapi.License(name="Apache 2 License"),
    ),
    validators=["flex", "ssv"],
    public=True,
    permission_classes=[permissions.AllowAny],
)

schema_cache_timeout = 60 * 5  # 5 minutes

swagger_urlpatterns = [
    path(
        "",
        schema_view.with_ui("swagger", cache_timeout=schema_cache_timeout),
        name="schema-swagger-ui",
    ),
    re_path(
        r"^swagger(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=schema_cache_timeout),
        name="schema-json",
    ),
    path(
        "redoc/",
        schema_view.with_ui("redoc", cache_timeout=schema_cache_timeout),
        name="schema-redoc",
    ),
]

urlpatterns_v1 = [
    path(
        "spotify/",
        include("fluctua_nft_backend.spotify.urls", namespace="spotify"),
    )
]

urlpatterns = swagger_urlpatterns + [
    path(settings.ADMIN_URL, admin.site.urls),
    path("api/v1/", include((urlpatterns_v1, "v1"))),
    path("check/", lambda request: HttpResponse("Ok"), name="check"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


if settings.DEBUG:
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
