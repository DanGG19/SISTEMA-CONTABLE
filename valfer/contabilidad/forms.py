from django import forms
from .models import *
from django.forms import inlineformset_factory
from decimal import Decimal
import datetime
from django.core.exceptions import ValidationError

class AsientoContableForm(forms.ModelForm):
    class Meta:
        model = AsientoContable
        fields = ['fecha', 'descripcion']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'descripcion': forms.Textarea(attrs={'rows': 2, 'class': 'form-textarea'}),
        }

class DetalleAsientoForm(forms.ModelForm):
    class Meta:
        model = DetalleAsiento
        fields = ['fecha', 'descripcion', 'cuenta', 'debe', 'haber']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['debe'].initial = Decimal('0.00')
        self.fields['haber'].initial = Decimal('0.00')

    def clean(self):
        cleaned_data = super().clean()
        debe = cleaned_data.get('debe')
        haber = cleaned_data.get('haber')

        if debe in [None, '']:
            cleaned_data['debe'] = Decimal('0.00')
        if haber in [None, '']:
            cleaned_data['haber'] = Decimal('0.00')

        return cleaned_data


DetalleAsientoFormSet = inlineformset_factory(
    AsientoContable,
    DetalleAsiento,
    form=DetalleAsientoForm,
    extra=2,
    can_delete=True
)

#pruebas para planillas

class PlanillaForm(forms.ModelForm):
    anio = forms.IntegerField(
        initial=datetime.date.today().year,
        widget=forms.NumberInput(attrs={'class': 'w-full border px-3 py-2 rounded'}),
        min_value=2020,
        max_value=2100
    )

    class Meta:
        model = Planilla
        fields = ['mes', 'anio', 'descripcion']
        widgets = {
            'mes': forms.Select(attrs={'class': 'w-full border px-3 py-2 rounded'}),
            'descripcion': forms.TextInput(attrs={'class': 'w-full border px-3 py-2 rounded'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        mes = cleaned_data.get('mes')
        anio = cleaned_data.get('anio')

        if mes and anio:
            if Planilla.objects.filter(mes=mes, anio=anio).exists():
                self.add_error(None, f"Ya existe una planilla registrada para {self.fields['mes'].choices[mes][1]} {anio}.")
        return cleaned_data



class DetallePlanillaForm(forms.ModelForm):
    class Meta:
        model = DetallePlanilla
        fields = ['empleado', 'dias_trabajados']


#Forms para Kardex de Inventario
class KardexMateriaPrimaForm(forms.ModelForm):
    class Meta:
        model = KardexMateriaPrima
        fields = ['fecha', 'tipo_movimiento', 'concepto', 'cantidad', 'costo_unitario']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
        }