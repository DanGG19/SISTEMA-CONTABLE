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
    path('iva/calcular/', views.calcular_iva, name='calcular_iva'),
    path('ajustes/nuevo/', views.crear_ajuste, name='crear_ajuste'),
    path('cierre-contable/', views.cierre_contable, name='cierre_contable'),
    path('libro-mayor/', views.libro_mayor, name='libro_mayor'),
    

    # Rutas para Planillas
    path('planillas/crear/', crear_planilla, name='crear_planilla'),
    path('planillas/<int:planilla_id>/detalles/', agregar_detalles, name='agregar_detalles'),
    path('planillas/<int:planilla_id>/ver/', ver_planilla, name='ver_planilla'),
    path('planillas/', listar_planillas, name='listar_planillas'),
    path('planillas/<int:planilla_id>/eliminar/', eliminar_planilla, name='eliminar_planilla'),

    #Para estados financieros
    path('estados-financieros/balance/', views.balance_general, name='balance_general'),
    path('estados-financieros/listar-balances/', views.listar_balances, name='listar_balances'),
    path('estados-financieros/resultado/', views.estado_resultados, name='estado_resultados'),
    path('estados-financieros/listar-resultados/', views.listar_resultados, name='listar_resultados'),
    path('estados-financieros/listar-resultados/resultados/<int:resultado_id>/', views.ver_resultado, name='ver_resultado'),

    #Inventario tipo de Kardex PEPS


    # Rutas para el módulo ABC


]
