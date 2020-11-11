from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from bills.views import BillViewSet

router = routers.DefaultRouter()
router.register(r'bill', BillViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
    path('admin/', admin.site.urls)
]
