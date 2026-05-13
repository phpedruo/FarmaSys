from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import time
from .models import Produto, Estoque, Loja, Pedido, ItemPedido, CarrinhoProduto
from decimal import Decimal
User = get_user_model()


# ==============================================================================
# CLASSE 01 - Testes da Página Inicial
# ==============================================================================
class Teste_01_PaginaInicial(TestCase):
    """Testa a view pagina_inicial e a exibição de promoções e destaques."""

    def setUp(self):
        self.client = Client()
        self.url = reverse('home')
        self.hoje = timezone.now().date()

    def tearDown(self):
        time.sleep(3)

    def test_01_deve_retornar_status_200(self):
        """Verifica se a página inicial carrega com sucesso."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_02_deve_usar_template_correto(self):
        """Verifica se o template correto é utilizado."""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'farmacia/home.html')

    def test_03_deve_exibir_promocoes_com_vencimento_em_30_dias(self):
        """Verifica se produtos vencendo em 30 dias aparecem como promoções."""
        prazo = self.hoje + timedelta(days=15)
        Produto.objects.create(
            nome="Produto Promo", codigo="PROMO-001",
            descricao="Produto promocional teste", categoria="Geral",
            preco_custo=Decimal("3.00"), preco=Decimal("10.00"),
            unidade_medida="unidade", dataValidade=prazo
        )
        response = self.client.get(self.url)
        self.assertIn('promocoes', response.context)
        self.assertEqual(len(response.context['promocoes']), 1)

    def test_04_deve_exibir_produtos_sem_vencimento_proximo(self):
        """Verifica se produtos sem vencimento próximo aparecem nos destaques."""
        prazo = self.hoje + timedelta(days=90)
        Produto.objects.create(
           nome="Produto Promo", codigo="PROMO-001",
           descricao="Produto promocional teste", categoria="Geral",
           preco_custo=Decimal("3.00"), preco=Decimal("10.00"),
           unidade_medida="unidade", dataValidade=prazo
        )
        response = self.client.get(self.url)
        self.assertIn('produtos', response.context)
        self.assertEqual(len(response.context['produtos']), 1)

    def test_05_deve_separar_promocoes_dos_destaques(self):
        """Verifica se promoções e destaques não se misturam."""
        # 1. Criamos um produto que VAI ser promoção (vencimento em 10 dias)
        # Usamos códigos e descrições ÚNICOS para não dar erro de Integrity
        Produto.objects.create(
            nome="Produto Promo Real", 
            codigo="UNIQUE-P-001", 
            descricao="Descrição Única Promo",
            categoria="Geral",
            preco_custo=Decimal("3.00"), 
            preco=Decimal("10.00"),
            unidade_medida="unidade", 
            dataValidade=self.hoje + timedelta(days=10)
        )

        # 2. Criamos um produto que NÃO vai ser promoção (vencimento em 60 dias)
        Produto.objects.create(
            nome="Produto Destaque Real", 
            codigo="UNIQUE-D-001", 
            descricao="Descrição Única Destaque",
            categoria="Geral",
            preco_custo=Decimal("5.00"), 
            preco=Decimal("15.00"),
            unidade_medida="unidade", 
            dataValidade=self.hoje + timedelta(days=60)
        )

        response = self.client.get(self.url)
        
        # Pegamos as listas de nomes do contexto
        nomes_promocoes = [p.nome for p in response.context['promocoes']]
        nomes_destaques = [p.nome for p in response.context['produtos']]

        # Verificações
        self.assertIn("Produto Promo Real", nomes_promocoes)
        self.assertNotIn("Produto Promo Real", nomes_destaques)
        self.assertIn("Produto Destaque Real", nomes_destaques)

# ==============================================================================
# CLASSE 02 - Testes da Página de Produtos
# ==============================================================================
class Teste_02_PaginaProdutos(TestCase):
    """Testa a view pagina_produtos e o filtro por categoria."""

    def setUp(self):
        self.client = Client()
        self.url = reverse('produtos')
        self.hoje = timezone.now().date()
        Produto.objects.create(
            nome="Dipirona",
            codigo="DIP-001", 
            descricao="Dipirona 500mg",
            categoria="analgesico", 
            preco_custo=Decimal("2.00"), 
            preco=Decimal("5.00"),
            unidade_medida="caixa", 
            dataValidade=self.hoje + timedelta(days=60)
        )
        Produto.objects.create(
            nome="Amoxicilina", 
            codigo="AMO-001", 
            descricao="Amoxicilina 500mg",
            categoria="antibiotico", 
            preco_custo=Decimal("8.00"), preco=Decimal("15.00"),
            unidade_medida="caixa", 
            dataValidade=self.hoje + timedelta(days=60)
        
        )

    def tearDown(self):
        time.sleep(0)

    def test_06_deve_retornar_status_200(self):
        """Verifica se a página de produtos carrega com sucesso."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_07_deve_listar_todos_os_produtos(self):
        """Verifica se todos os produtos são listados sem filtro."""
        response = self.client.get(self.url)
        self.assertEqual(len(response.context['produtos']), 2)

    def test_08_deve_filtrar_por_categoria(self):
        """Verifica se o filtro por categoria funciona corretamente."""
        response = self.client.get(self.url, {'categoria': 'analgesico'})
        produtos = response.context['produtos']
        self.assertEqual(len(produtos), 1)
        self.assertEqual(produtos[0].nome, "Dipirona")

    def test_09_deve_retornar_lista_de_categorias(self):
        """Verifica se as categorias disponíveis são passadas ao contexto."""
        response = self.client.get(self.url)
        categorias = list(response.context['categorias'])
        self.assertIn('analgesico', categorias)
        self.assertIn('antibiotico', categorias)

    def test_10_deve_retornar_vazio_para_categoria_inexistente(self):
        """Verifica que filtro com categoria inexistente retorna lista vazia."""
        response = self.client.get(self.url, {'categoria': 'inexistente'})
        self.assertEqual(len(response.context['produtos']), 0)


# ==============================================================================
# CLASSE 03 - Testes da Página de Ofertas
# ==============================================================================
class Teste_03_PaginaOfertas(TestCase):
    """Testa a view pagina_ofertas com produtos próximos ao vencimento."""

    def setUp(self):
        self.client = Client()
        self.url = reverse('promocoes')
        self.hoje = timezone.now().date()

    def tearDown(self):
        time.sleep(0)

    def test_11_deve_retornar_status_200(self):
        """Verifica se a página de ofertas carrega com sucesso."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_12_deve_usar_template_correto(self):
        """Verifica se o template de promoções é utilizado."""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'farmacia/promocoes.html')

    def test_13_deve_listar_apenas_produtos_vencendo_em_30_dias(self):
        """Verifica se apenas produtos com vencimento em até 30 dias são exibidos."""
        Produto.objects.create(
            nome="Promo", 
            codigo="PROMO-002", 
            descricao="Produto promo oferta",
            categoria="Geral", 
            preco_custo=Decimal("2.00"), 
            preco=Decimal("5.00"),
            unidade_medida="unidade", 
            dataValidade=self.hoje + timedelta(days=10)
        
        )
        Produto.objects.create(
            nome="Normal", 
            codigo="NORM-001", 
            descricao="Produto normal sem oferta",
            categoria="Geral", 
            preco_custo=Decimal("4.00"), 
            preco=Decimal("8.00"),
            unidade_medida="unidade", 
            dataValidade=self.hoje + timedelta(days=60)
        
        )
        response = self.client.get(self.url)
        nomes = [p.nome for p in response.context['produtos']]
        self.assertIn("Promo", nomes)
        self.assertNotIn("Normal", nomes)


# ==============================================================================
# CLASSE 04 - Testes do Estoque (acesso restrito a staff)
# ==============================================================================
class Teste_04_ConsultaEstoque(TestCase):
    """Testa a view consulta_estoque com controle de acesso."""

    def setUp(self):
        self.client = Client()
        self.url = reverse('consulta_estoque')
        self.admin = User.objects.create_user(username="admin", password="admin@123", is_staff=True)
        self.user = User.objects.create_user(username="comum", password="comum@123")

    def tearDown(self):
        time.sleep(0)

    def test_14_deve_redirecionar_usuario_nao_autenticado(self):
        """Verifica se usuário não logado é redirecionado."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_15_deve_redirecionar_usuario_sem_permissao_staff(self):
        """Verifica se usuário comum não tem acesso ao estoque."""
        self.client.login(username="comum", password="comum@123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_16_deve_permitir_acesso_a_usuario_staff(self):
        """Verifica se usuário staff consegue acessar o estoque."""
        self.client.login(username="admin", password="admin@123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_17_deve_exibir_totais_no_contexto(self):
        """Verifica se os totais de produtos são passados ao contexto."""
        self.client.login(username="admin", password="admin@123")
        response = self.client.get(self.url)
        self.assertIn('total_produtos', response.context)
        self.assertIn('total_vencendo', response.context)
        self.assertIn('total_baixo', response.context)
        self.assertIn('total_lojas', response.context)


# ==============================================================================
# CLASSE 05 - Testes do Registro de Usuário
# ==============================================================================
class Teste_05_Register(TestCase):
    """Testa a view register para criação de novos usuários."""

    def setUp(self):
        self.client = Client()
        self.url = reverse('register')

    def tearDown(self):
        time.sleep(0)

    def test_18_deve_retornar_status_200_no_get(self):
        """Verifica se a página de registro carrega via GET."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_19_deve_criar_usuario_com_dados_validos(self):
        """Verifica se um novo usuário é criado com dados válidos."""
        response = self.client.post(self.url, {
            'username': 'novousuario',
            'password1': 'Senha@Segura123',
            'password2': 'Senha@Segura123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='novousuario').exists())

    def test_20_deve_redirecionar_para_login_apos_registro(self):
        """Verifica se após o registro o usuário é redirecionado para o login."""
        response = self.client.post(self.url, {
            'username': 'novousuario',
            'password1': 'Senha@Segura123',
            'password2': 'Senha@Segura123',
        })
        self.assertRedirects(response, reverse('login'))

    def test_21_nao_deve_criar_usuario_com_senhas_diferentes(self):
        """Verifica se senhas divergentes impedem o cadastro."""
        self.client.post(self.url, {
            'username': 'invalido',
            'password1': 'Senha@Segura123',
            'password2': 'SenhaDiferente456',
        })
        self.assertFalse(User.objects.filter(username='invalido').exists())


# ==============================================================================
# CLASSE 06 - Testes do Carrinho de Compras
# ==============================================================================
class Teste_06_Carrinho(TestCase):
    """Testa as views de adição, atualização e remoção de itens do carrinho."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="cliente", password="cliente@123")
        self.client.login(username="cliente", password="cliente@123")
        self.hoje = timezone.now().date()
        self.produto = Produto.objects.create(
            nome="Paracetamol", 
            codigo="PAR-001", 
            descricao="Paracetamol 750mg",
            categoria="Analgesicos", 
            preco_custo=Decimal("3.00"), 
            preco=Decimal("8.00"),
            unidade_medida="caixa", 
            dataValidade=self.hoje + timedelta(days=60)
        )

    def tearDown(self):
        time.sleep(0)

    def test_22_deve_adicionar_produto_ao_carrinho(self):
        """Verifica se um produto é adicionado ao carrinho corretamente."""
        url = reverse('adicionar_carrinho', args=[self.produto.id])
        self.client.post(url, {'quantidade': 2})
        item = CarrinhoProduto.objects.get(usuario=self.user, produto=self.produto)
        self.assertEqual(item.quantidade, 2)

    def test_23_deve_acumular_quantidade_ao_adicionar_produto_existente(self):
        """Verifica se a quantidade acumula ao adicionar um produto já no carrinho."""
        CarrinhoProduto.objects.create(usuario=self.user, produto=self.produto, quantidade=1)
        url = reverse('adicionar_carrinho', args=[self.produto.id])
        self.client.post(url, {'quantidade': 3})
        item = CarrinhoProduto.objects.get(usuario=self.user, produto=self.produto)
        self.assertEqual(item.quantidade, 4)

    def test_24_deve_exibir_itens_do_carrinho(self):
        """Verifica se os itens do carrinho são exibidos na página."""
        CarrinhoProduto.objects.create(usuario=self.user, produto=self.produto, quantidade=2)
        response = self.client.get(reverse('carrinho'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['itens']), 1)

    def test_25_deve_atualizar_quantidade_do_item_no_carrinho(self):
        """Verifica se a quantidade de um item é atualizada corretamente."""
        item = CarrinhoProduto.objects.create(usuario=self.user, produto=self.produto, quantidade=1)
        url = reverse('atualizar_item_carrinho', args=[item.id])
        self.client.post(url, {'quantidade': 5})
        item.refresh_from_db()
        self.assertEqual(item.quantidade, 5)

    def test_26_deve_remover_item_do_carrinho(self):
        """Verifica se um item é removido do carrinho após solicitação."""
        item = CarrinhoProduto.objects.create(usuario=self.user, produto=self.produto, quantidade=1)
        url = reverse('remover_item_carrinho', args=[item.id])
        self.client.post(url)
        self.assertFalse(CarrinhoProduto.objects.filter(id=item.id).exists())

    def test_27_nao_deve_adicionar_ao_carrinho_sem_login(self):
        """Verifica se usuário não autenticado é redirecionado ao tentar adicionar."""
        self.client.logout()
        url = reverse('adicionar_carrinho', args=[self.produto.id])
        response = self.client.post(url, {'quantidade': 1})
        self.assertEqual(response.status_code, 302)


# ==============================================================================
# CLASSE 07 - Testes do Checkout
# ==============================================================================
class Teste_07_Checkout(TestCase):
    """Testa a view checkout com validação de estoque e criação de pedido."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="comprador", password="comprador@123")
        self.client.login(username="comprador", password="comprador@123")
        self.url = reverse('checkout')
        self.hoje = timezone.now().date()
        self.loja = Loja.objects.create(nome="Loja Central", ativa=True)
        self.produto = Produto.objects.create(
            nome="Ibuprofeno", 
            codigo="IBU-001", 
            descricao="Ibuprofeno 400mg",
            categoria="Analgesicos", 
            preco_custo=Decimal("5.00"), 
            preco=Decimal("12.00"),
            unidade_medida="caixa", 
            dataValidade=self.hoje + timedelta(days=60)
        )
        self.estoque = Estoque.objects.create(produto=self.produto, loja=self.loja, quantidade=50)
        CarrinhoProduto.objects.create(usuario=self.user, produto=self.produto, quantidade=2)

    def tearDown(self):
        time.sleep(0)

    def test_28_deve_retornar_status_200_no_get(self):
        """Verifica se a página de checkout carrega via GET."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_29_deve_redirecionar_carrinho_vazio_para_produtos(self):
        """Verifica se carrinho vazio redireciona para a página de produtos."""
        CarrinhoProduto.objects.filter(usuario=self.user).delete()
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('produtos'))

    def test_30_deve_criar_pedido_com_estoque_suficiente(self):
        """Verifica se o pedido é criado quando há estoque suficiente."""
        self.client.post(self.url, {'loja': self.loja.id})
        self.assertEqual(Pedido.objects.filter(usuario=self.user).count(), 1)

    def test_31_deve_descontar_estoque_apos_pedido(self):
        """Verifica se o estoque é decrementado após a criação do pedido."""
        self.client.post(self.url, {'loja': self.loja.id})
        self.estoque.refresh_from_db()
        self.assertEqual(self.estoque.quantidade, 48)

    def test_32_deve_limpar_carrinho_apos_checkout(self):
        """Verifica se o carrinho é esvaziado após o pedido ser finalizado."""
        self.client.post(self.url, {'loja': self.loja.id})
        self.assertFalse(CarrinhoProduto.objects.filter(usuario=self.user).exists())

    def test_33_nao_deve_criar_pedido_com_estoque_insuficiente(self):
        """Verifica se pedido é bloqueado quando o estoque é insuficiente."""
        self.estoque.quantidade = 1
        self.estoque.save()
        self.client.post(self.url, {'loja': self.loja.id})
        self.assertEqual(Pedido.objects.filter(usuario=self.user).count(), 0)


# ==============================================================================
# CLASSE 08 - Testes de Pedidos do Usuário
# ==============================================================================
class Teste_08_MeusPedidos(TestCase):
    """Testa a listagem e detalhe de pedidos do usuário."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="usuario", password="usuario@123")
        self.client.login(username="usuario", password="usuario@123")
        self.loja = Loja.objects.create(nome="Loja Sul", ativa=True)
        self.pedido = Pedido.objects.create(usuario=self.user, loja=self.loja)

    def tearDown(self):
        time.sleep(0)

    def test_34_deve_listar_pedidos_do_usuario(self):
        """Verifica se os pedidos do usuário são listados corretamente."""
        response = self.client.get(reverse('meus_pedidos'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.pedido, response.context['pedidos'])

    def test_35_deve_filtrar_pedidos_por_status(self):
        """Verifica se o filtro por status funciona na listagem de pedidos."""
        self.pedido.status = 'PENDENTE'
        self.pedido.save()
        response = self.client.get(reverse('meus_pedidos'), {'status': 'PENDENTE'})
        self.assertIn(self.pedido, response.context['pedidos'])

    def test_36_deve_exibir_detalhe_do_pedido(self):
        """Verifica se a página de detalhe do pedido carrega corretamente."""
        url = reverse('detalhe_pedido', args=[self.pedido.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['pedido'], self.pedido)

    def test_37_nao_deve_exibir_pedido_de_outro_usuario(self):
        """Verifica se um usuário não consegue ver pedidos de outro usuário."""
        outro = User.objects.create_user(username="outro", password="outro@123")
        pedido_outro = Pedido.objects.create(usuario=outro, loja=self.loja)
        url = reverse('detalhe_pedido', args=[pedido_outro.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


# ==============================================================================
# CLASSE 09 - Testes de Repetir Compra
# ==============================================================================
class Teste_09_RepetirCompra(TestCase):
    """Testa a view repetir_compra para reordenar itens de um pedido anterior."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="recomprador", password="recomprador@123")
        self.client.login(username="recomprador", password="recomprador@123")
        self.hoje = timezone.now().date()
        self.loja = Loja.objects.create(nome="Loja Norte", ativa=True)
        self.produto = Produto.objects.create(
            nome="Vitamina C", 
            codigo="VIT-C-001", 
            descricao="Vitamina C 1000mg",
            categoria="Suplementos", 
            preco_custo=Decimal("4.00"), 
            preco=Decimal("9.00"),
            unidade_medida="caixa", 
            dataValidade=self.hoje + timedelta(days=60)
        )
        Estoque.objects.create(produto=self.produto, loja=self.loja, quantidade=20)
        self.pedido = Pedido.objects.create(usuario=self.user, loja=self.loja)
        ItemPedido.objects.create(
            pedido=self.pedido, produto=self.produto, quantidade=2, preco_unitario=9.00
        )

    def tearDown(self):
        time.sleep(0)

    def test_38_deve_adicionar_itens_do_pedido_ao_carrinho(self):
        """Verifica se os itens do pedido anterior são adicionados ao carrinho."""
        url = reverse('repetir_compra', args=[self.pedido.id])
        self.client.post(url)
        self.assertTrue(CarrinhoProduto.objects.filter(usuario=self.user, produto=self.produto).exists())

    def test_39_deve_acumular_quantidade_se_item_ja_estiver_no_carrinho(self):
        """Verifica se a quantidade acumula ao repetir compra com item já no carrinho."""
        CarrinhoProduto.objects.create(usuario=self.user, produto=self.produto, quantidade=1)
        url = reverse('repetir_compra', args=[self.pedido.id])
        self.client.post(url)
        item = CarrinhoProduto.objects.get(usuario=self.user, produto=self.produto)
        self.assertEqual(item.quantidade, 3)

    def test_40_nao_deve_adicionar_produto_sem_estoque(self):
        """Verifica se produtos sem estoque são ignorados ao repetir a compra."""
        Estoque.objects.filter(produto=self.produto).update(quantidade=0)
        url = reverse('repetir_compra', args=[self.pedido.id])
        self.client.post(url)
        self.assertFalse(CarrinhoProduto.objects.filter(usuario=self.user, produto=self.produto).exists())

    def test_41_nao_deve_repetir_compra_de_outro_usuario(self):
        """Verifica se um usuário não consegue repetir pedido de outro usuário."""
        outro = User.objects.create_user(username="intruso", password="intruso@123")
        pedido_outro = Pedido.objects.create(usuario=outro, loja=self.loja)
        url = reverse('repetir_compra', args=[pedido_outro.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_42_deve_redirecionar_get_para_meus_pedidos(self):
        """Verifica se uma requisição GET é redirecionada para meus_pedidos."""
        url = reverse('repetir_compra', args=[self.pedido.id])
        response = self.client.get(url)
        self.assertRedirects(response, reverse('meus_pedidos'))
        

# --- Teste de descontos por Quantidade ---

# CLASSE 10 - Testes de Desconto por Quantidade

class Teste_10_DescontoPorQuantidade(TestCase):
    """
    Testa a lógica de desconto progressivo por quantidade do model Produto
    e o cálculo correto do subtotal no CarrinhoProduto.

    Regras de negócio:
        - quantidade < 3   → sem desconto     (100% do preço)
        - quantidade >= 3  → 5% de desconto   (95% do preço)
        - quantidade >= 5  → 10% de desconto  (90% do preço)
        - quantidade >= 10 → 20% de desconto  (80% do preço)
    """

    def setUp(self):
        self.user = User.objects.create_user(username="desconto_user", password="desc@123")
        self.hoje = timezone.now().date()
        self.produto = Produto.objects.create(
            nome="Vitamina D",
            codigo="VIT-D-001",
            descricao="Suplemento vitamina D 1000UI",
            dataValidade=self.hoje + timedelta(days=90),
            categoria="Suplementos",
            preco_custo=Decimal("5.00"),
            preco=Decimal("10.00"),
            unidade_medida="caixa",
        )

    def tearDown(self):
        time.sleep(0)

    # Testes do método obterPrecoPorQuantidade (no model Produto)

    def test_43_preco_sem_desconto_para_quantidade_1(self):
        """Quantidade 1 não deve ter desconto — preço cheio."""
        preco = self.produto.obterPrecoPorQuantidade(1)
        self.assertEqual(preco, Decimal("10.00"))

    def test_44_preco_sem_desconto_para_quantidade_2(self):
        """Quantidade 2 também não deve ter desconto — abaixo do mínimo."""
        preco = self.produto.obterPrecoPorQuantidade(2)
        self.assertEqual(preco, Decimal("10.00"))

    def test_45_preco_com_5_porcento_de_desconto_para_quantidade_3(self):
        """Quantidade 3 deve aplicar 5% de desconto — R$ 9.50."""
        preco = self.produto.obterPrecoPorQuantidade(3)
        self.assertEqual(preco, Decimal("10.00") * Decimal("0.95"))

    def test_46_preco_com_5_porcento_de_desconto_para_quantidade_4(self):
        """Quantidade 4 ainda deve aplicar apenas 5% — abaixo de 5 unidades."""
        preco = self.produto.obterPrecoPorQuantidade(4)
        self.assertEqual(preco, Decimal("10.00") * Decimal("0.95"))

    def test_47_preco_com_10_porcento_de_desconto_para_quantidade_5(self):
        """Quantidade 5 deve aplicar 10% de desconto — R$ 9.00."""
        preco = self.produto.obterPrecoPorQuantidade(5)
        self.assertEqual(preco, Decimal("10.00") * Decimal("0.90"))

    def test_48_preco_com_10_porcento_de_desconto_para_quantidade_9(self):
        """Quantidade 9 ainda deve aplicar 10% — abaixo de 10 unidades."""
        preco = self.produto.obterPrecoPorQuantidade(9)
        self.assertEqual(preco, Decimal("10.00") * Decimal("0.90"))

    def test_49_preco_com_20_porcento_de_desconto_para_quantidade_10(self):
        """Quantidade 10 deve aplicar 20% de desconto — R$ 8.00."""
        preco = self.produto.obterPrecoPorQuantidade(10)
        self.assertEqual(preco, Decimal("10.00") * Decimal("0.80"))

    def test_50_preco_com_20_porcento_de_desconto_para_quantidade_grande(self):
        """Quantidade 50 deve manter o desconto máximo de 20%."""
        preco = self.produto.obterPrecoPorQuantidade(50)
        self.assertEqual(preco, Decimal("10.00") * Decimal("0.80"))


    # Testes do calcular_subtotal (no model CarrinhoProduto)    

    def test_51_subtotal_sem_desconto_para_2_unidades(self):
        """
        Subtotal de 2 unidades = preço cheio × 2.
        2 × R$ 10.00 = R$ 20.00
        """
        item = CarrinhoProduto(
            usuario=self.user,
            produto=self.produto,
            quantidade=2,
        )
        self.assertEqual(item.calcular_subtotal(), Decimal("20.00"))

    def test_52_subtotal_com_desconto_de_5_porcento_para_3_unidades(self):
        """
        Subtotal de 3 unidades com 5% de desconto.
        3 × R$ 9.50 = R$ 28.50
        """
        item = CarrinhoProduto(
            usuario=self.user,
            produto=self.produto,
            quantidade=3,
        )
        esperado = Decimal("10.00") * Decimal("0.95") * 3
        self.assertEqual(item.calcular_subtotal(), esperado)

    def test_53_subtotal_com_desconto_de_10_porcento_para_5_unidades(self):
        """
        Subtotal de 5 unidades com 10% de desconto.
        5 × R$ 9.00 = R$ 45.00
        """
        item = CarrinhoProduto(
            usuario=self.user,
            produto=self.produto,
            quantidade=5,
        )
        esperado = Decimal("10.00") * Decimal("0.90") * 5
        self.assertEqual(item.calcular_subtotal(), esperado)

    def test_54_subtotal_com_desconto_de_20_porcento_para_10_unidades(self):
        """
        Subtotal de 10 unidades com 20% de desconto.
        10 × R$ 8.00 = R$ 80.00
        """
        item = CarrinhoProduto(
            usuario=self.user,
            produto=self.produto,
            quantidade=10,
        )
        esperado = Decimal("10.00") * Decimal("0.80") * 10
        self.assertEqual(item.calcular_subtotal(), esperado)

    def test_55_desconto_aplicado_no_checkout_para_quantidade_10(self):
        """
        Verifica que o checkout usa o preço com desconto de 20%
        ao criar o ItemPedido para quantidade >= 10.
        """
        loja = Loja.objects.create(
            nome="Loja Teste Desconto",
            endereco="Rua A",
            numero="1",
            bairro="Centro",
            cidade="Recife",
            estado="PE",
            cep="50000-000",
            ativa=True,
        )
        Estoque.objects.create(produto=self.produto, loja=loja, quantidade=50)
        CarrinhoProduto.objects.create(
            usuario=self.user, produto=self.produto, quantidade=10
        )

        self.client = Client()
        self.client.login(username="desconto_user", password="desc@123")
        self.client.post(reverse('checkout'), {'loja': loja.id})

        item_pedido = ItemPedido.objects.get(
            pedido__usuario=self.user,
            produto=self.produto,
        )
        self.assertEqual(item_pedido.preco_unitario, Decimal("10.00") * Decimal("0.80"))

    def test_56_sem_desconto_no_checkout_para_quantidade_2(self):
        """
        Verifica que o checkout usa preço cheio para quantidade < 3.
        """
        loja = Loja.objects.create(
            nome="Loja Teste Sem Desconto",
            endereco="Rua B",
            numero="2",
            bairro="Boa Vista",
            cidade="Recife",
            estado="PE",
            cep="50000-001",
            ativa=True,
        )
        Estoque.objects.create(produto=self.produto, loja=loja, quantidade=50)
        CarrinhoProduto.objects.create(
            usuario=self.user, produto=self.produto, quantidade=2
        )

        self.client = Client()
        self.client.login(username="desconto_user", password="desc@123")
        self.client.post(reverse('checkout'), {'loja': loja.id})

        item_pedido = ItemPedido.objects.get(
            pedido__usuario=self.user,
            produto=self.produto,
        )
        self.assertEqual(item_pedido.preco_unitario, Decimal("10.00"))