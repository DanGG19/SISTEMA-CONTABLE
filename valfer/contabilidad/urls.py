from django.urls import path
from . import views
from .views import *

urlpatterns = [

    # Rutas para autenticación
    path('login',views.login_view, name='login'),
    path('logout', views.logout_view, name='logout'),

    path('', views.home, name='home'),
    path('catalogo/', catalogo_cuentas, name='catalogo'),
    path('asientos/count/<str:fecha>', views.contar_asientos_por_fecha, name='contar_asientos_por_fecha'),
    path('asientos/nuevo/', views.crear_asiento_contable, name='crear_asiento_contable'),
    path('asientos/', views.listar_asientos, name='listar_asientos'),
    path('asientos/<int:asiento_id>/', views.ver_asiento, name='ver_asiento'),
    path('asientos/<int:asiento_id>/eliminar/', views.eliminar_asiento, name='eliminar_asiento'),
    path('libro-mayor/', views.libro_mayor, name='libro_mayor'),
    path('consolidar-iva', views.vista_consolidar_iva, name='vista_consolidar_iva'),
    
    #Para estados financieros
    path('hoja_trabajo/', views.hoja_trabajo, name='hoja_trabajo'),
    

    # Rutas para Planillas
    path('planillas/crear/', crear_planilla, name='crear_planilla'),
    path('planillas/<int:planilla_id>/detalles/', agregar_detalles, name='agregar_detalles'),
    path('planillas/<int:planilla_id>/ver/', ver_planilla, name='ver_planilla'),
    path('planillas/', listar_planillas, name='listar_planillas'),
    path('planillas/<int:planilla_id>/eliminar/', eliminar_planilla, name='eliminar_planilla'),




    #Kardex home
    path('kardex/', views.kardex_home, name='kardex_home'),

    #Inventario tipo de Kardex PEPS
    path('kardex/<int:materia_prima_id>/', views.kardex_materia_prima_list, name='kardex_materia_prima_list'),
    path('kardex/<int:materia_prima_id>/nuevo/', views.kardex_materia_prima_nuevo, name='kardex_materia_prima_nuevo'),
    #Listar Kardex de Producto Terminado
    path('kardex/productos_terminados/', views.listar_kardex_productos_terminados, name='listar_kardex_productos_terminados'),
    #embolsar café
    path('kardex/embolsar_cafe/', views.fabricar_embolsar_cafe, name='fabricar_embolsar_cafe'),
    #mezclar café
    path('kardex/mezclar_licor/', views.fabricar_mezcla_licor, name='fabricar_mezcla_licor'),
    #embotellar café
    path('kardex/embotellar_licor/', views.fabricar_embotellar_licor, name='fabricar_embotellar_licor'),
    #Inventario tipo de Kardex para café PEPS para Producto Terminado
    path('kardex/producto/<int:producto_id>/', views.kardex_producto_terminado, name='kardex_producto_terminado'),

    #Inventario venta de productos terminados
    path('ventas/nueva/', views.vender_producto_terminado, name='vender_producto_terminado'),

    



]
