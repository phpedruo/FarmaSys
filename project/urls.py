from django.contrib import admin
from django.urls import path
from farmacia import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.pagina_inicial, name='home'),
    path('produtos/', views.pagina_produtos, name='produtos'),  
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='farmacia/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('estoque/', views.consulta_estoque, name='consulta_estoque'),
    path('promocoes/', views.pagina_ofertas, name='promocoes'),
]
