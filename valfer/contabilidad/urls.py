from django.urls import path
from . import views
from .views import *

urlpatterns = [
    path('', views.home, name='home'),
    path('catalogo/', catalogo_cuentas, name='catalogo'),
    path('asientos/count/<str:fecha>', views.contar_asientos_por_fecha, name='contar_asientos_por_fecha'),
    path('asientos/nuevo/', views.crear_asiento_contable, name='crear_asiento_contable'),
    path('asientos/', views.listar_asientos, name='listar_asientos'),
    path('asientos/<int:asiento_id>/', views.ver_asiento, name='ver_asiento'),
    path('asientos/<int:asiento_id>/eliminar/', views.eliminar_asiento, name='eliminar_asiento'),

]
