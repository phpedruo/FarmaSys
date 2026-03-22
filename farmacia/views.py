from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView


from .models import Produto, Loja

def pagina_inicial(request):
    """Landing page com produtos em destaque e informações"""
    from django.db.models import Sum
    
    produtos_mais_pedidos = Produto.objects.annotate(
        total_vendido=Sum('itempedido__quantidade')
    ).filter(
        total_vendido__isnull=False
    ).order_by('-total_vendido')[:3]
    
    if not produtos_mais_pedidos.exists():
        produtos_destaque = Produto.objects.all()[:3]
    else:
        produtos_destaque = produtos_mais_pedidos
    
    # 2. Lógica das lojas
    lojas = Loja.objects.filter(ativa=True)[:3]
    
    contexto = {
        'produtos_destaque': produtos_destaque,
        'lojas': lojas,
    }
    return render(request, 'farmacia/home.html', contexto)

class CustomLoginView(LoginView):
    template_name = 'farmacia/login.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)
    
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')  # Após cadastrar, manda para o login
    else:
        form = UserCreationForm()
    return render(request, 'farmacia/register.html', {'form': form})