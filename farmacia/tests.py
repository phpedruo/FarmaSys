from unittest.mock import patch
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Estoque, Loja, Produto, Pedido, ItemPedido, CarrinhoProduto


class ConsultaEstoqueTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		cls.url = reverse('consulta_estoque')

		cls.loja = Loja.objects.create(
			nome='Loja Centro',
			endereco='Rua A',
			numero='100',
			bairro='Centro',
			cidade='Recife',
			estado='PE',
			cep='50000-000',
			ativa=True,
		)

		cls.produto_estoque_ok = Produto.objects.create(
			nome='Dipirona',
			codigo='DIP001',
			descricao='Analgésico Dipirona',
			categoria='Analgésico',
			preco_custo='2.00',
			preco='4.00',
			unidade_medida='caixa',
		)
		cls.produto_estoque_baixo = Produto.objects.create(
			nome='Ibuprofeno',
			codigo='IBU001',
			descricao='Anti-inflamatório Ibuprofeno',
			categoria='Anti-inflamatório',
			preco_custo='3.00',
			preco='6.00',
			unidade_medida='caixa',
		)

		cls.estoque_ok = Estoque.objects.create(
			produto=cls.produto_estoque_ok,
			loja=cls.loja,
			quantidade=30,
		)
		cls.estoque_baixo = Estoque.objects.create(
			produto=cls.produto_estoque_baixo,
			loja=cls.loja,
			quantidade=10,
		)

		cls.superuser = User.objects.create_superuser(
			username='gerente',
			email='gerente@example.com',
			password='senhaforte123',
		)
		cls.usuario_comum = User.objects.create_user(
			username='funcionario',
			password='senhaforte123',
		)

	def test_usuario_anonimo_sem_acesso(self):
		response = self.client.get(self.url)
		self.assertEqual(response.status_code, 302)
		self.assertRedirects(response, f"{reverse('login')}?next={self.url}")

	def test_usuario_autenticado_nao_superusuario_sem_acesso(self):
		self.client.login(username='funcionario', password='senhaforte123')
		response = self.client.get(self.url)
		self.assertEqual(response.status_code, 403)
		self.assertIn(
			'Acesso negado. Apenas gerentes podem consultar o estoque.',
			response.content.decode('utf-8'),
		)

	def test_busca_parcial_estoque_maior_ou_igual_30_mensagem_correta(self):
		self.client.login(username='gerente', password='senhaforte123')
		response = self.client.get(self.url, {'nome': 'Dipi'})

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Dipirona')
		self.assertContains(response, 'Produto em estoque')
		self.assertNotContains(
			response,
			'Estoque abaixo do mínimo. Iniciar o processo de compras.',
		)

	def test_busca_parcial_estoque_menor_30_mensagem_correta(self):
		self.client.login(username='gerente', password='senhaforte123')
		response = self.client.get(self.url, {'codigo': 'IBU'})

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Ibuprofeno')
		self.assertContains(
			response,
			'Estoque abaixo do mínimo. Iniciar o processo de compras.',
		)

	def test_busca_sem_resultados_exibe_erro_e_sem_tabela(self):
		self.client.login(username='gerente', password='senhaforte123')
		response = self.client.get(self.url, {'nome': 'Inexistente'})

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Erro ao acessar o Estoque')
		self.assertNotContains(response, '<table', html=False)

	def test_falha_simulada_consulta_exibe_mesma_mensagem(self):
		self.client.login(username='gerente', password='senhaforte123')

		with patch('farmacia.views.Estoque.objects.select_related', side_effect=Exception('falha')):
			response = self.client.get(self.url, {'nome': 'Dipi'})

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Erro ao acessar o Estoque')
		self.assertNotContains(response, '<table', html=False)


class PedidosECarrinhoTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		cls.user = User.objects.create_user(username='cliente1', password='senha12345')
		cls.outro_user = User.objects.create_user(username='cliente2', password='senha12345')

		cls.loja = Loja.objects.create(
			nome='Loja Boa Viagem',
			endereco='Av Exemplo',
			numero='45',
			bairro='Boa Viagem',
			cidade='Recife',
			estado='PE',
			cep='51000-000',
			ativa=True,
		)

		validade_futura = date.today() + timedelta(days=60)
		cls.produto_a = Produto.objects.create(
			nome='Paracetamol 500mg',
			codigo='PARA500',
			descricao='Analgesico paracetamol',
			dataValidade=validade_futura,
			categoria='Medicamento',
			preco_custo='3.00',
			preco='7.50',
			unidade_medida='caixa',
		)
		cls.produto_b = Produto.objects.create(
			nome='Vitamina C',
			codigo='VITC100',
			descricao='Suplemento vitamina c',
			dataValidade=validade_futura,
			categoria='Suplemento',
			preco_custo='8.00',
			preco='15.00',
			unidade_medida='frasco',
		)

		Estoque.objects.create(produto=cls.produto_a, loja=cls.loja, quantidade=20)
		Estoque.objects.create(produto=cls.produto_b, loja=cls.loja, quantidade=0)

		cls.pedido_user = Pedido.objects.create(usuario=cls.user, loja=cls.loja)
		ItemPedido.objects.create(
			pedido=cls.pedido_user,
			produto=cls.produto_a,
			quantidade=2,
			preco_unitario=Decimal('7.50'),
		)
		ItemPedido.objects.create(
			pedido=cls.pedido_user,
			produto=cls.produto_b,
			quantidade=1,
			preco_unitario=Decimal('15.00'),
		)

		cls.pedido_outro = Pedido.objects.create(usuario=cls.outro_user, loja=cls.loja)
		ItemPedido.objects.create(
			pedido=cls.pedido_outro,
			produto=cls.produto_a,
			quantidade=1,
			preco_unitario=Decimal('7.50'),
		)

	def test_meus_pedidos_lista_apenas_pedidos_do_usuario_logado(self):
		self.client.login(username='cliente1', password='senha12345')

		response = self.client.get(reverse('meus_pedidos'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, f'#{self.pedido_user.id}')
		self.assertNotContains(response, f'#{self.pedido_outro.id}')

	def test_repetir_compra_adiciona_disponiveis_e_ignora_indisponiveis(self):
		self.client.login(username='cliente1', password='senha12345')

		response = self.client.post(reverse('repetir_compra', args=[self.pedido_user.id]))

		self.assertRedirects(response, reverse('carrinho'))
		item_carrinho = CarrinhoProduto.objects.filter(usuario=self.user, produto=self.produto_a).first()
		self.assertIsNotNone(item_carrinho)
		self.assertEqual(item_carrinho.quantidade, 2)
		self.assertFalse(CarrinhoProduto.objects.filter(usuario=self.user, produto=self.produto_b).exists())

	def test_checkout_cria_pedido_limpa_carrinho_e_debita_estoque(self):
		self.client.login(username='cliente1', password='senha12345')

		CarrinhoProduto.objects.create(usuario=self.user, produto=self.produto_a, quantidade=3)

		response = self.client.post(reverse('checkout'), {'loja': self.loja.id})

		self.assertEqual(response.status_code, 302)
		self.assertIn('/pedidos/', response.url)

		novo_pedido = Pedido.objects.filter(usuario=self.user).order_by('-id').first()
		self.assertIsNotNone(novo_pedido)
		self.assertEqual(novo_pedido.itens.count(), 1)
		self.assertFalse(CarrinhoProduto.objects.filter(usuario=self.user).exists())

		estoque_atual = Estoque.objects.get(produto=self.produto_a, loja=self.loja)
		self.assertEqual(estoque_atual.quantidade, 17)
