from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from .models import Produto, Estoque, Loja
from django.utils import timezone
from datetime import timedelta


def is_staff(user):
    return user.is_staff


#Home
def pagina_inicial(request):
    hoje = timezone.now().date()
    prazo = hoje + timedelta(days=30)

    # Produtos com vencimento nos próximos 30 dias
    promocoes = Produto.objects.filter(dataValidade__range=[hoje, prazo])[:6]

    # Destaques gerais (excluindo os que já estão em promoção)
    produtos = Produto.objects.exclude(
        dataValidade__range=[hoje, prazo]
    )[:8]

    return render(request, 'farmacia/home.html', {
        'promocoes': promocoes,
        'produtos': produtos,
    })


#Produtos
def pagina_produtos(request):
    hoje = timezone.now().date()
    prazo = hoje + timedelta(days=30)

    produtos = Produto.objects.all()

    categoria_ativa = request.GET.get('categoria', '')
    if categoria_ativa:
        produtos = produtos.filter(categoria=categoria_ativa)

    categorias = Produto.objects.values_list('categoria', flat=True).distinct().order_by('categoria')

    return render(request, 'farmacia/produtos.html', {
        'produtos': produtos,
        'categorias': categorias,
        'categoria_ativa': categoria_ativa,
    })


def pagina_ofertas(request):
    hoje = timezone.now().date()
    prazo = hoje + timedelta(days=30)

    produtos = Produto.objects.filter(dataValidade__range=[hoje, prazo])

    return render(request, 'farmacia/promocoes.html', {
        'produtos': produtos,
    })


#Estoque(admin tem acesso)
@login_required
@user_passes_test(is_staff)
def consulta_estoque(request):
    estoques = Produto.objects.all()
    hoje = timezone.now().date()
    prazo = hoje + timedelta(days=30)

    total_produtos = estoques.count()
    total_vencendo = estoques.filter(dataValidade__range=[hoje, prazo]).count()
    total_baixo    = sum(1 for p in estoques if 0 < p.estoque_total() < 30)
    total_lojas    = Loja.objects.filter(ativa=True).count()

    return render(request, 'farmacia/consulta_estoque.html', {
        'estoques': estoques,
        'total_produtos': total_produtos,
        'total_vencendo': total_vencendo,
        'total_baixo': total_baixo,
        'total_lojas': total_lojas,
    })

#register
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Conta criada com sucesso! Faça login para continuar.')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'farmacia/register.html', {'form': form})