from django.db import models
from django.db.models import CheckConstraint, Q
from django.core.validators import MinValueValidator
from django.conf import settings



class Loja(models.Model):
    nome = models.CharField(max_length=100)
    endereco = models.CharField(max_length=200)
    numero = models.CharField(max_length=10)
    bairro = models.CharField(max_length=100)
    cidade = models.CharField(max_length=100)
    estado = models.CharField(max_length=2)
    cep = models.CharField(max_length=9)
    prazo_retirada_dias = models.IntegerField(default=1)
    ativa = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nome} - {self.cidade}/{self.estado}"

        
class Produto(models.Model):
	nome = models.CharField(max_length=30, unique=True)
	codigo = models.CharField(max_length=30, unique=True)
	descricao = models.CharField(max_length=200, default="", unique=True)
	categoria = models.CharField(max_length=50)
	preco_custo = models.DecimalField(
		max_digits=10, 
		decimal_places=2,
		validators=[MinValueValidator(0)] 
	)
	preco = models.DecimalField(
		max_digits=10, 
		decimal_places=2,
		validators=[MinValueValidator(0)] 
	)
	unidade_medida = models.CharField(max_length=20)

	class Meta:
		constraints = [
            models.CheckConstraint(condition=~models.Q(codigo=""), name='codigo_nao_vazio'),
            models.CheckConstraint(condition=~models.Q(descricao=""), name='descricao_nao_vazia'),
            models.CheckConstraint(condition=~models.Q(categoria=""), name='categoria_nao_vazia'),
            models.CheckConstraint(condition=~models.Q(unidade_medida=""), name='unidade_medida_nao_vazia'),
        ]

	def __str__(self):
		return f"{self.codigo} - {self.descricao} - {self.categoria}"
	
	def estoque_total(self):
		from django.db.models import Sum
		total = self.estoque_set.aggregate(Sum('quantidade'))['quantidade__sum']
		return total if total is not None else 0


class Pedido(models.Model):
    # O comprador (quem está logado)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    # Onde ele vai buscar 
    loja = models.ForeignKey('Loja', on_delete=models.CASCADE)
    
    data_criacao = models.DateTimeField(auto_now_add=True)
    
    STATUS_CHOICES = [
        ('PENDENTE', 'Aguardando Retirada'),
        ('CONCLUIDO', 'Retirado'),
        ('CANCELADO', 'Cancelado'),
    ]
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDENTE')

    def __str__(self):
        return f"Pedido #{self.id} - {self.usuario.username} na {self.loja.nome}"

    def calcular_total(self):
        """Soma o valor de todos os itens vinculados a este pedido"""
        total = sum(item.calcular_subtotal() for item in self.itens.all())
        return total
    

class ItemPedido(models.Model):
    """Item de um pedido - cópia dos produtos do carrinho no momento da compra"""
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='itens')
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantidade = models.PositiveIntegerField()
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)  # Preço no momento da compra
    
    def __str__(self):
        return f"{self.quantidade}x {self.produto.nome} (Pedido #{self.pedido.id})"
    
    def calcular_subtotal(self):
        return self.preco_unitario * self.quantidade
    
class Estoque(models.Model):
    ESTOQUE_MINIMO_PADRAO = 30

    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    loja = models.ForeignKey(Loja, on_delete=models.CASCADE) 
    quantidade = models.PositiveIntegerField()
    data_ultima_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        # Garante que cada produto tenha apenas um registro de quantidade por loja
        unique_together = ('produto', 'loja')

    def __str__(self):
        return f"{self.produto.nome} na {self.loja.nome}: {self.quantidade}"

    def esta_abaixo_estoque_minimo(self, minimo=None):
        limite = minimo if minimo is not None else self.ESTOQUE_MINIMO_PADRAO
        return self.quantidade < limite

    def mensagem_status_estoque(self, minimo=None):
        if self.esta_abaixo_estoque_minimo(minimo=minimo):
            return "Estoque abaixo do mínimo. Iniciar o processo de compras."
        return "Produto em estoque"

    @classmethod
    def abaixo_estoque_minimo(cls, minimo=None):
        limite = minimo if minimo is not None else cls.ESTOQUE_MINIMO_PADRAO
        return cls.objects.filter(quantidade__lt=limite)
# Create your models here.
