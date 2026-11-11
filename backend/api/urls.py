"""Rutas de la API REST del backend Django."""
from django.urls import path
from . import views

urlpatterns = [
    path('analizar-funcion/', views.analizar_funcion_view, name='analizar_funcion'),
    path('capitulo-1/ejecutar/', views.capitulo_1_ejecutar, name='cap1_ejecutar'),
    path('capitulo-1/comparar/', views.capitulo_1_comparar, name='cap1_comparar'),
    path('capitulo-2/ejecutar/', views.capitulo_2_ejecutar, name='cap2_ejecutar'),
    path('capitulo-2/comparar/', views.capitulo_2_comparar, name='cap2_comparar'),
    path('capitulo-3/ejecutar/', views.capitulo_3_ejecutar, name='cap3_ejecutar'),
    path('capitulo-3/comparar/', views.capitulo_3_comparar, name='cap3_comparar'),
    path('capitulo-3/almacenamiento/', views.capitulo_3_almacenamiento, name='cap3_almacenamiento'),
]

