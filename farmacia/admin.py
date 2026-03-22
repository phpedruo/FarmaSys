from django.contrib import admin
from .models import Produto, Loja, Pedido, ItemPedido, Estoque

admin.site.register(Produto)
admin.site.register(Loja)
admin.site.register(Pedido)
admin.site.register(ItemPedido)
admin.site.register(Estoque)
