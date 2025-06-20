# Generated by Django 5.2.1 on 2025-06-20 23:43

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AsientoContable',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateField()),
                ('descripcion', models.TextField()),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Empleado',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('dui', models.CharField(max_length=10)),
                ('nit', models.CharField(max_length=17)),
                ('cargo', models.CharField(max_length=100)),
                ('salario_base', models.DecimalField(decimal_places=2, max_digits=10)),
            ],
        ),
        migrations.CreateModel(
            name='MateriaPrima',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('unidad_medida', models.CharField(max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='Planilla',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mes', models.IntegerField(choices=[(1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'), (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'), (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')])),
                ('anio', models.IntegerField()),
                ('descripcion', models.CharField(max_length=255)),
                ('creada_en', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='ProcesoProduccion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateField()),
                ('tipo', models.CharField(choices=[('mezcla', 'Mezcla Licor'), ('embazado', 'Embazado'), ('tostado', 'Tostado')], max_length=30)),
                ('cantidad_producida', models.DecimalField(decimal_places=2, max_digits=12)),
                ('costo_total', models.DecimalField(decimal_places=2, max_digits=12)),
            ],
        ),
        migrations.CreateModel(
            name='ProductoTerminado',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('unidad_medida', models.CharField(max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='CuentaContable',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo', models.CharField(max_length=20, unique=True)),
                ('nombre', models.CharField(max_length=255)),
                ('tipo', models.CharField(choices=[('activo', 'Activo'), ('pasivo', 'Pasivo'), ('patrimonio', 'Patrimonio'), ('costo', 'Costo'), ('gasto', 'Gasto'), ('ingreso', 'Ingreso'), ('liquidadora', 'Liquidadora')], max_length=50)),
                ('nivel', models.IntegerField()),
                ('padre', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contabilidad.cuentacontable')),
            ],
        ),
        migrations.CreateModel(
            name='DetalleAsiento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateField(blank=True, null=True)),
                ('descripcion', models.CharField(blank=True, max_length=255)),
                ('debe', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('haber', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('asiento', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contabilidad.asientocontable')),
                ('cuenta', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contabilidad.cuentacontable')),
            ],
        ),
        migrations.CreateModel(
            name='KardexMateriaPrima',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateField()),
                ('tipo_movimiento', models.CharField(choices=[('entrada', 'Entrada'), ('salida', 'Salida'), ('proceso', 'Consumo Proceso')], max_length=20)),
                ('concepto', models.CharField(blank=True, max_length=255, null=True)),
                ('cantidad', models.DecimalField(decimal_places=2, max_digits=12)),
                ('costo_unitario', models.DecimalField(decimal_places=2, max_digits=12)),
                ('total', models.DecimalField(decimal_places=2, max_digits=12)),
                ('saldo_cantidad', models.DecimalField(decimal_places=2, max_digits=12)),
                ('saldo_total', models.DecimalField(decimal_places=2, max_digits=12)),
                ('materia_prima', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contabilidad.materiaprima')),
            ],
        ),
        migrations.CreateModel(
            name='DetallePlanilla',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dias_trabajados', models.IntegerField()),
                ('salario', models.DecimalField(decimal_places=2, max_digits=10)),
                ('afp', models.DecimalField(decimal_places=2, max_digits=10)),
                ('isss', models.DecimalField(decimal_places=2, max_digits=10)),
                ('total_pagado', models.DecimalField(decimal_places=2, max_digits=10)),
                ('total_costo_empleador', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('empleado', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contabilidad.empleado')),
                ('planilla', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='detalles', to='contabilidad.planilla')),
            ],
        ),
        migrations.CreateModel(
            name='ConsumoMateriaPrima',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cantidad_usada', models.DecimalField(decimal_places=2, max_digits=12)),
                ('costo_asignado', models.DecimalField(decimal_places=2, max_digits=12)),
                ('materia_prima', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contabilidad.materiaprima')),
                ('proceso', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='consumos', to='contabilidad.procesoproduccion')),
            ],
        ),
        migrations.AddField(
            model_name='procesoproduccion',
            name='producto_terminado',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contabilidad.productoterminado'),
        ),
        migrations.CreateModel(
            name='ProcesoFabricacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('embolsar_cafe', 'Embolsar Café'), ('mezclar_licor', 'Mezcla Café con Licor'), ('embotellar_licor', 'Embotellado Café con Licor')], max_length=30)),
                ('fecha', models.DateField(auto_now_add=True)),
                ('cantidad_producida', models.IntegerField()),
                ('gramos_usados', models.DecimalField(decimal_places=2, max_digits=10)),
                ('quintales_usados', models.DecimalField(decimal_places=2, max_digits=10)),
                ('costo_materia_prima', models.DecimalField(decimal_places=2, max_digits=12)),
                ('costo_mano_obra', models.DecimalField(decimal_places=2, max_digits=12)),
                ('cif', models.DecimalField(decimal_places=2, max_digits=12)),
                ('costo_total', models.DecimalField(decimal_places=2, max_digits=12)),
                ('producto_final', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contabilidad.productoterminado')),
            ],
        ),
        migrations.CreateModel(
            name='KardexProductoTerminado',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateField()),
                ('tipo_movimiento', models.CharField(choices=[('ingreso', 'Ingreso Proceso'), ('salida', 'Venta')], max_length=20)),
                ('concepto', models.CharField(blank=True, max_length=255, null=True)),
                ('cantidad', models.DecimalField(decimal_places=2, max_digits=12)),
                ('costo_unitario', models.DecimalField(decimal_places=2, max_digits=12)),
                ('precio_venta_unitario', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('total', models.DecimalField(decimal_places=2, max_digits=12)),
                ('saldo_cantidad', models.DecimalField(decimal_places=2, max_digits=12)),
                ('saldo_total', models.DecimalField(decimal_places=2, max_digits=12)),
                ('producto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contabilidad.productoterminado')),
            ],
        ),
    ]
