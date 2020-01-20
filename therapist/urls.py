"""therapist URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Import the include() function: from django.conf.urls import url, include
    3. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import url, include
from django.contrib import admin
from app.views import parse_csv, login, get_sessions, update_sessions

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^create_session/', parse_csv),
    url(r'^advanced_filters/', include('advanced_filters.urls')),
    url(r'^login', login),
    url(r'^sessions/$', get_sessions),
    url(r'^session/update/', update_sessions)
]
admin.site.site_header = "Functional Learning Centre Inc"
admin.site.site_title = "Functional Learning Centre Inc"
admin.site.index_title = "Functional Learning Centre Inc"

