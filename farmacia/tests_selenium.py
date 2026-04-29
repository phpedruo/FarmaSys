import time
import tkinter as tk
from threading import Thread
from django.contrib.auth import get_user_model
from django.test import LiveServerTestCase
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

User = get_user_model()

class TimerGUI:
    def __init__(self, test_name, seconds=3):
        self.test_name = test_name
        self.seconds = seconds
    def show(self):
        self.root = tk.Tk()
        self.root.title("Executando Teste")
        self.root.geometry("400x150")
        self.root.configure(bg="#1e1e2e")
        tk.Label(self.root, text=self.test_name, font=("Arial", 11, "bold"), bg="#1e1e2e", fg="#cdd6f4", wraplength=380).pack(pady=15)
        self.timer_label = tk.Label(self.root, text=f"Proximo teste em: {self.seconds}s", font=("Arial", 14), bg="#1e1e2e", fg="#a6e3a1")
        self.timer_label.pack(pady=10)
        self.root.after(0, self._countdown, self.seconds)
        self.root.mainloop()
    def _countdown(self, remaining):
        if remaining > 0:
            self.timer_label.config(text=f"Proximo teste em: {remaining}s")
            self.root.after(1000, self._countdown, remaining - 1)
        else:
            self.root.destroy()

def mostrar_timer(test_name, seconds=3):
    gui = TimerGUI(test_name, seconds)
    thread = Thread(target=gui.show)
    thread.start()
    thread.join()

class BaseTestCase(LiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        opts = Options()
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--window-size=1280,800")
        service = Service(ChromeDriverManager().install())
        cls.driver = webdriver.Chrome(service=service, options=opts)
        cls.wait = WebDriverWait(cls.driver, 10)
    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "driver"):
            cls.driver.quit()
        super().tearDownClass()
    def tearDown(self):
        mostrar_timer(self._testMethodName, seconds=3)
    def abrir_pagina(self, path):
        self.driver.get(f"{self.live_server_url}{path}")

class Teste_01_Login(BaseTestCase):
    def test_01_deve_carregar_pagina_de_login(self):
        self.abrir_pagina("/login/")
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        self.assertIn("login", self.driver.current_url.lower())
    def test_02_deve_fazer_login_com_sucesso(self):
        User.objects.create_user(username="teste", password="Senha@123")
        self.abrir_pagina("/login/")
        self.driver.find_element(By.NAME, "username").send_keys("teste")
        self.driver.find_element(By.NAME, "password").send_keys("Senha@123")
        self.driver.find_element(By.TAG_NAME, "form").submit()
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        self.assertNotIn("login", self.driver.current_url.lower())
    def test_03_nao_deve_fazer_login_com_senha_errada(self):
        User.objects.create_user(username="teste2", password="Senha@123")
        self.abrir_pagina("/login/")
        self.driver.find_element(By.NAME, "username").send_keys("teste2")
        self.driver.find_element(By.NAME, "password").send_keys("SenhaErrada")
        self.driver.find_element(By.TAG_NAME, "form").submit()
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        self.assertIn("login", self.driver.current_url.lower())

class Teste_02_Navegacao(BaseTestCase):
    def test_04_deve_carregar_pagina_inicial(self):
        self.abrir_pagina("/")
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        self.assertNotEqual(self.driver.title, "")
    def test_05_deve_carregar_pagina_de_produtos(self):
        self.abrir_pagina("/produtos/")
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        self.assertIn("produtos", self.driver.current_url.lower())
    def test_06_deve_carregar_pagina_de_ofertas(self):
        self.abrir_pagina("/promocoes/")
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        self.assertIn("promocoes", self.driver.current_url.lower())
