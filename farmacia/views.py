from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView
from django.http import HttpResponseForbidden


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
    resultados = []
    mensagem = ''

    try:
        estoques = Estoque.objects.select_related('produto', 'loja').all()

        if nome or codigo:
            filtro = Q()
            if nome:
                filtro |= Q(produto__nome__icontains=nome)
            if codigo:
                filtro |= Q(produto__codigo__icontains=codigo)
            estoques = estoques.filter(filtro)

        estoques = estoques.filter(quantidade__lt=Estoque.ESTOQUE_MINIMO_PADRAO)

        resultados = [
            {
                'produto_nome': estoque.produto.nome,
                'produto_codigo': estoque.produto.codigo,
                'quantidade': estoque.quantidade,
                'data_ultima_atualizacao': estoque.data_ultima_atualizacao,
                'mensagem': 'Estoque abaixo do mínimo. Iniciar o processo de compras.',
            }
            for estoque in estoques
        ]

        if not resultados:
            mensagem = 'Erro ao acessar o Estoque'
    except Exception:
        resultados = []
        mensagem = 'Erro ao acessar o Estoque'

    contexto = {
        'nome': nome,
        'codigo': codigo,
        'resultados': resultados,
        'mensagem': mensagem,
    }
    return render(request, 'farmacia/consulta_estoque.html', contexto)