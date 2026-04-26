from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.db import transaction
from .models import Produto, Estoque, Loja, Pedido, ItemPedido, CarrinhoProduto
from .forms import AdicionarCarrinhoForm, AtualizarCarrinhoForm, CheckoutForm
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


@login_required
def meus_pedidos(request):
    status_ativo = request.GET.get('status', '').strip().upper()
    pedidos = Pedido.objects.filter(usuario=request.user).select_related('loja').prefetch_related('itens__produto').order_by('-data_criacao')

    if status_ativo:
        pedidos = pedidos.filter(status=status_ativo)

    return render(request, 'farmacia/meus_pedidos.html', {
        'pedidos': pedidos,
        'status_ativo': status_ativo,
        'status_choices': Pedido.STATUS_CHOICES,
    })


@login_required
def detalhe_pedido(request, pedido_id):
    pedido = get_object_or_404(
        Pedido.objects.select_related('loja').prefetch_related('itens__produto'),
        id=pedido_id,
        usuario=request.user,
    )
    return render(request, 'farmacia/detalhe_pedido.html', {
        'pedido': pedido,
        'itens': pedido.itens.all(),
    })


@login_required
def adicionar_carrinho(request, produto_id):
    if request.method != 'POST':
        return redirect('produtos')

    produto = get_object_or_404(Produto, id=produto_id)
    form = AdicionarCarrinhoForm(request.POST)

    if not form.is_valid():
        messages.error(request, 'Quantidade invalida para adicionar ao carrinho.')
        return redirect('produtos')

    quantidade = form.cleaned_data['quantidade']
    item, created = CarrinhoProduto.objects.get_or_create(
        usuario=request.user,
        produto=produto,
        defaults={'quantidade': quantidade},
    )

    if not created:
        item.quantidade += quantidade
        item.save(update_fields=['quantidade'])

    messages.success(request, f'{produto.nome} foi adicionado ao carrinho.')
    return redirect('carrinho')


@login_required
def carrinho(request):
    itens = list(
        CarrinhoProduto.objects.filter(usuario=request.user)
        .select_related('produto')
        .order_by('-data_adicionado')
    )
    total = sum(item.calcular_subtotal() for item in itens)
    return render(request, 'farmacia/carrinho.html', {
        'itens': itens,
        'total': total,
        'form_quantidade': AtualizarCarrinhoForm(),
    })


@login_required
def atualizar_item_carrinho(request, item_id):
    if request.method != 'POST':
        return redirect('carrinho')

    item = get_object_or_404(CarrinhoProduto, id=item_id, usuario=request.user)
    form = AtualizarCarrinhoForm(request.POST)

    if not form.is_valid():
        messages.error(request, 'Nao foi possivel atualizar a quantidade informada.')
        return redirect('carrinho')

    item.quantidade = form.cleaned_data['quantidade']
    item.save(update_fields=['quantidade'])
    messages.success(request, f'Quantidade de {item.produto.nome} atualizada no carrinho.')
    return redirect('carrinho')


@login_required
def remover_item_carrinho(request, item_id):
    if request.method != 'POST':
        return redirect('carrinho')

    item = get_object_or_404(CarrinhoProduto, id=item_id, usuario=request.user)
    nome_produto = item.produto.nome
    item.delete()
    messages.success(request, f'{nome_produto} foi removido do carrinho.')
    return redirect('carrinho')


@login_required
@transaction.atomic
def checkout(request):
    itens = list(CarrinhoProduto.objects.filter(usuario=request.user).select_related('produto'))

    if not itens:
        messages.warning(request, 'Seu carrinho esta vazio. Adicione produtos para continuar.')
        return redirect('produtos')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)

        if form.is_valid():
            loja = form.cleaned_data['loja']
            indisponiveis = []

            for item in itens:
                estoque = Estoque.objects.filter(produto=item.produto, loja=loja).first()
                quantidade_disponivel = estoque.quantidade if estoque else 0
                if quantidade_disponivel < item.quantidade:
                    indisponiveis.append((item.produto.nome, quantidade_disponivel, item.quantidade))

            if indisponiveis:
                for nome, disponivel, solicitada in indisponiveis:
                    messages.error(
                        request,
                        f'Estoque insuficiente para {nome}: disponivel {disponivel}, solicitado {solicitada}.',
                    )
                return redirect('carrinho')

            pedido = Pedido.objects.create(usuario=request.user, loja=loja)

            for item in itens:
                ItemPedido.objects.create(
                    pedido=pedido,
                    produto=item.produto,
                    quantidade=item.quantidade,
                    preco_unitario=item.produto.preco,
                )

                estoque = Estoque.objects.select_for_update().get(produto=item.produto, loja=loja)
                estoque.quantidade -= item.quantidade
                estoque.save(update_fields=['quantidade', 'data_ultima_atualizacao'])

            CarrinhoProduto.objects.filter(usuario=request.user).delete()
            messages.success(request, f'Pedido #{pedido.id} criado com sucesso.')
            return redirect('detalhe_pedido', pedido_id=pedido.id)
    else:
        form = CheckoutForm()

    total = sum(item.calcular_subtotal() for item in itens)
    return render(request, 'farmacia/checkout.html', {
        'itens': itens,
        'total': total,
        'form': form,
    })


@login_required
def repetir_compra(request, pedido_id):
    if request.method != 'POST':
        return redirect('meus_pedidos')

    pedido = get_object_or_404(
        Pedido.objects.prefetch_related('itens__produto'),
        id=pedido_id,
        usuario=request.user,
    )

    adicionados = 0
    indisponiveis = []

    for item_pedido in pedido.itens.all():
        if not Estoque.objects.filter(
            produto=item_pedido.produto,
            loja__ativa=True,
            quantidade__gt=0,
        ).exists():
            indisponiveis.append(item_pedido.produto.nome)
            continue

        item_carrinho, created = CarrinhoProduto.objects.get_or_create(
            usuario=request.user,
            produto=item_pedido.produto,
            defaults={'quantidade': item_pedido.quantidade},
        )
        if not created:
            item_carrinho.quantidade += item_pedido.quantidade
            item_carrinho.save(update_fields=['quantidade'])
        adicionados += 1

    if adicionados:
        messages.success(request, f'{adicionados} item(ns) do pedido foram adicionados ao carrinho.')
    if indisponiveis:
        lista = ', '.join(indisponiveis)
        messages.warning(request, f'Itens indisponiveis no momento: {lista}.')
    if not adicionados and not indisponiveis:
        messages.info(request, 'Nao ha itens para repetir neste pedido.')

    return redirect('carrinho')