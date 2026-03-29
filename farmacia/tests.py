from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Estoque, Loja, Produto


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
