from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView
from django.http import HttpResponseForbidden, JsonResponse


from .models import Produto, Loja, Estoque

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


@login_required
def consulta_estoque(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Acesso negado. Apenas gerentes podem consultar o estoque.")

    nome = request.GET.get('nome', '').strip()
    codigo = request.GET.get('codigo', '').strip()

    estoques = Estoque.objects.select_related('produto', 'loja').all()

    if nome:
        estoques = estoques.filter(produto__nome__icontains=nome)

    if codigo:
        estoques = estoques.filter(produto__codigo__icontains=codigo)

    resultados = [
        {
            'produto_nome': estoque.produto.nome,
            'produto_codigo': estoque.produto.codigo,
            'quantidade': estoque.quantidade,
            'data_ultima_atualizacao': estoque.data_ultima_atualizacao.isoformat(),
            'mensagem': estoque.mensagem_status_estoque(),
        }
        for estoque in estoques
    ]

    return JsonResponse({'total': len(resultados), 'resultados': resultados})