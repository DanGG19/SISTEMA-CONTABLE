from django import forms
from .models import AsientoContable, DetalleAsiento, CuentaContable
from django.forms import inlineformset_factory
from decimal import Decimal

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