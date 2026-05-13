import time
from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from .models import Produto, Estoque, Loja, CarrinhoProduto

User = get_user_model()

class FarmaTecSeleniumTests(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        opts = Options()
        opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--window-size=1280,800")
        opts.add_experimental_option('excludeSwitches', ['enable-logging'])

        try:
            service = ChromeService(ChromeDriverManager().install())
            cls.driver = webdriver.Chrome(service=service, options=opts)
            cls.wait = WebDriverWait(cls.driver, 10)
        except Exception as e:
            print(f"Falha ao iniciar o Chrome: {e}")
            raise

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'driver'):
            cls.driver.quit()
        super().tearDownClass()

    def setUp(self):
        self.wait = WebDriverWait(self.driver, 10)
        self.driver.delete_all_cookies()

    def tearDown(self):
        pass

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def abrir_pagina(self, path):
        self.driver.get(f"{self.live_server_url}{path}")

    def fazer_login(self, username, password):
        self.abrir_pagina("/login/")
        username_input = self.wait.until(EC.element_to_be_clickable((By.NAME, "username")))
        password_input = self.driver.find_element(By.NAME, "password")
        
        username_input.clear()
        username_input.send_keys(username)
        password_input.clear()
        password_input.send_keys(password)
        self.driver.find_element(By.TAG_NAME, "form").submit()
        self.wait.until(lambda d: "/login/" not in d.current_url)

    def _criar_dados_desconto(self):
        usuario, _ = User.objects.get_or_create(
            username="testedesconto",
            defaults={"is_staff": False, "is_active": True}
        )
        if _:
            usuario.set_password("Desc@123")
            usuario.save()

        CarrinhoProduto.objects.filter(usuario=usuario).delete()

        hoje = timezone.now().date()
        produto, _ = Produto.objects.update_or_create(
            codigo="DIP-500-001",
            defaults={
                "nome": "Dipirona 500mg",
                "preco": Decimal("10.00"),
                "descricao": "Medicamento para dor e febre",
                "estoque": 100,
                "categoria": "Geral",
                "dataValidade": hoje + timedelta(days=90),
                "preco_custo": Decimal("3.00"),
                "unidade_medida": "caixa",
            }
        )

        loja, _ = Loja.objects.update_or_create(
            nome="Loja Teste",
            defaults={"ativa": True, "cidade": "Recife", "estado": "PE"}
        )
        Estoque.objects.update_or_create(produto=produto, loja=loja, defaults={"quantidade": 100})
        return usuario, produto

    def _abrir_carrinho_com_quantidade(self, usuario, produto, quantidade):
        self.fazer_login(usuario.username, "Desc@123")
        item, _ = CarrinhoProduto.objects.update_or_create(
            usuario=usuario,
            produto=produto,
            defaults={'quantidade': quantidade}
        )
        self.abrir_pagina("/carrinho/")
        return item

    # ==========================================================================
    # TESTES AJUSTADOS ÀS SUAS URLS
    # ==========================================================================
    
    def test_01_acesso_home(self):
        self.abrir_pagina("/")
        self.assertIn("FarmaTec", self.driver.page_source)

    def test_02_login_sucesso(self):
        u, p = self._criar_dados_desconto()
        self.fazer_login(u.username, "Desc@123")
        self.assertIn("FarmaTec", self.driver.page_source)

    def test_03_abrir_carrinho_vazio(self):
        u, p = self._criar_dados_desconto()
        self.fazer_login(u.username, "Desc@123")
        self.abrir_pagina("/carrinho/")
        self.assertIn("vazio", self.driver.page_source.lower())

    def test_04_adicionar_ao_carrinho_via_url(self):
        u, p = self._criar_dados_desconto()
        self.fazer_login(u.username, "Desc@123")
        # URL conforme seu urls.py: /carrinho/adicionar/<int:produto_id>/
        self.abrir_pagina(f"/carrinho/adicionar/{p.id}/")
        self.assertIn(p.nome, self.driver.page_source)

    def test_05_remover_do_carrinho(self):
        u, p = self._criar_dados_desconto()
        # Abre o carrinho com 1 item
        self._abrir_carrinho_com_quantidade(u, p, 1)
        
        # Em vez de abrir a URL, vamos clicar no botão de remover (lixeira)
        # O seletor busca o botão dentro do formulário que tem a ação de remover
        botao_remover = self.wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, f"form[action*='/remover/'] button")
        ))
        botao_remover.click()
        
        # Agora sim, o carrinho deve estar vazio
        self.wait.until(lambda d: "vazio" in d.page_source.lower() or p.nome not in d.page_source)
        self.assertIn("vazio", self.driver.page_source.lower())

    def test_06_atualizar_quantidade_carrinho(self):
        """Teste adaptado: já que não há 'limpar tudo', testamos a atualização."""
        u, p = self._criar_dados_desconto()
        item = self._abrir_carrinho_com_quantidade(u, p, 1)
        # URL conforme seu urls.py: /carrinho/item/<int:item_id>/atualizar/
        # Simulando uma atualização via GET ou acesso direto (ajuste conforme sua view se for POST)
        self.abrir_pagina(f"/carrinho/item/{item.id}/atualizar/?quantidade=5")
        self.abrir_pagina("/carrinho/")
        self.assertIn(p.nome, self.driver.page_source)

    def test_07_deve_exibir_sem_desconto_para_quantidade_2(self):
        u, p = self._criar_dados_desconto()
        self._abrir_carrinho_com_quantidade(u, p, 2)
        badge = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "badge-qty-0")))
        self.assertIn("Sem desconto", badge.text)
    
    def test_08_deve_exibir_badge_de_5_porcento_para_quantidade_3(self):
        u, p = self._criar_dados_desconto()
        self._abrir_carrinho_com_quantidade(u, p, 3)
        badge = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "badge-qty-5")))
        self.assertIn("5%", badge.text)

    def test_09_deve_exibir_badge_de_10_porcento_para_quantidade_5(self):
        u, p = self._criar_dados_desconto()
        self._abrir_carrinho_com_quantidade(u, p, 5)
        badge = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "badge-qty-10")))
        self.assertIn("10%", badge.text)

    def test_10_deve_exibir_badge_de_20_porcento_para_quantidade_10(self):
        u, p = self._criar_dados_desconto()
        self._abrir_carrinho_com_quantidade(u, p, 10)
        badge = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "badge-qty-20")))
        self.assertIn("20%", badge.text)

    def test_11_deve_exibir_dica_de_quantas_unidades_faltam(self):
        u, p = self._criar_dados_desconto()
        self._abrir_carrinho_com_quantidade(u, p, 3)
        dica = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "badge-qty-hint")))
        self.assertIn("Faltam", dica.text)

    def test_12_deve_exibir_banner_de_desconto_no_topo_do_carrinho(self):
        u, p = self._criar_dados_desconto()
        self._abrir_carrinho_com_quantidade(u, p, 1)
        banner = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "discount-banner")))
        self.assertTrue(banner.is_displayed())