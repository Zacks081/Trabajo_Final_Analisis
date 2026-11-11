"""Rutas principales de Django: sirve la API REST en /api/ y la SPA en React en /."""
from django.urls import include, path
from api.views import spa_index

urlpatterns = [
    path('api/', include('api.urls')),
    path('', spa_index, name='spa_index'),
]

