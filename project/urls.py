from django.contrib import admin
from django.urls import path
from farmacia import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.pagina_inicial, name='home'),
    path('produtos/', views.pagina_produtos, name='produtos'),  
    path('meus-pedidos/', views.meus_pedidos, name='meus_pedidos'),
    path('pedidos/<int:pedido_id>/', views.detalhe_pedido, name='detalhe_pedido'),
    path('pedidos/<int:pedido_id>/repetir/', views.repetir_compra, name='repetir_compra'),
    path('carrinho/', views.carrinho, name='carrinho'),
    path('carrinho/adicionar/<int:produto_id>/', views.adicionar_carrinho, name='adicionar_carrinho'),
    path('carrinho/item/<int:item_id>/atualizar/', views.atualizar_item_carrinho, name='atualizar_item_carrinho'),
    path('carrinho/item/<int:item_id>/remover/', views.remover_item_carrinho, name='remover_item_carrinho'),
    path('checkout/', views.checkout, name='checkout'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='farmacia/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('estoque/', views.consulta_estoque, name='consulta_estoque'),
    path('promocoes/', views.pagina_ofertas, name='promocoes'),
]
