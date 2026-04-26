from django import forms

from .models import Loja


class AdicionarCarrinhoForm(forms.Form):
    quantidade = forms.IntegerField(min_value=1, initial=1)


class AtualizarCarrinhoForm(forms.Form):
    quantidade = forms.IntegerField(min_value=1)


class CheckoutForm(forms.Form):
    loja = forms.ModelChoiceField(
        queryset=Loja.objects.filter(ativa=True),
        empty_label='Selecione a loja para retirada',
    )
