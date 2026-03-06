from bot_app.views import web_app_shop
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('shop/', web_app_shop, name='shop')
    
]



