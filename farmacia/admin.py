from django.contrib import admin
from .models import Produto, Loja, Pedido, ItemPedido, Estoque, CarrinhoProduto

# 1. Configuração do Produto (Com a lógica de alerta)
@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'codigo', 'dataValidade', 'status_validade')
    list_filter = ('dataValidade', 'categoria')

    def status_validade(self, obj):
        if obj.proximoDataDeValidade():
            return "PRÓXIMO AO VENCIMENTO"
        return "REGULAR"
    
    status_validade.short_description = 'Status de Validade'

# 2. Registro dos demais modelos
admin.site.register(Loja)
admin.site.register(Pedido)
admin.site.register(ItemPedido)
admin.site.register(Estoque)


@admin.register(CarrinhoProduto)
class CarrinhoProdutoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'produto', 'quantidade', 'data_adicionado')
    list_filter = ('data_adicionado', 'usuario')
    search_fields = ('usuario__username', 'produto__nome')