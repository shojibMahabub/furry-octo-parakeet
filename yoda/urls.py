from django.conf.urls import url, include
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
    url(r'^api/', include(('tuitions.urls', 'tuitions'), namespace='tuitions')),
    url(r'^', include(('tuitions.landing_urls', 'landing'), namespace='landing')),
]
