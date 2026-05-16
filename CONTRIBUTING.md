# 🤝 Guia de Contribuição (CONTRIBUTING.md)

Bem-vindo ao projeto! Este guia vai te conduzir passo a passo para montar o ambiente de desenvolvimento e contribuir com o projeto de forma correta.

---

## 📋 Pré-requisitos

Antes de começar, certifique-se de ter instalado em sua máquina:

- [Python 3.8+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/)
- pip (geralmente já vem com o Python)

---

## 🚀 Passo a Passo para Configurar o Ambiente

### 1. Clonar o Repositório

```bash
git clone https://github.com/Nick182-n/FarmaTec.git
cd seu-repositorio
```

---

### 2. Criar e Ativar o Ambiente Virtual (venv)

O ambiente virtual isola as dependências do projeto para não conflitar com outras instalações do seu computador.

**No Windows:**

```bash
python -m venv venv
.\venv\Scripts\activate
```

**No Linux/macOS:**

```bash
python3 -m venv venv
source venv/bin/activate
```

> ✅ Você saberá que deu certo quando aparecer `(venv)` no início da linha do seu terminal.

---

### 3. Instalar as Dependências

Com o ambiente ativado, instale todas as bibliotecas necessárias (Django, Selenium, etc.):

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

### 4. Configurar o Banco de Dados (SQLite)

Gere as tabelas do banco de dados local executando as migrações do Django:

```bash
python manage.py migrate
```

---

### 5. Criar um Usuário Administrador (Opcional)

Para acessar o painel do Django (`/admin`) e cadastrar produtos manualmente:

```bash
python manage.py createsuperuser
```

> Siga as instruções na tela para definir usuário, e-mail e senha.

---

### 6. Rodar o Servidor Local

Agora, inicie o servidor de desenvolvimento:

```bash
python manage.py runserver
```

Abra o navegador e acesse: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

## 🧪 Executando os Testes

Para garantir que nenhuma alteração quebrou o sistema (especialmente as regras de carrinho e descontos), execute os testes automatizados.

### Rodar os Testes do Selenium (Headless)

```bash
python manage.py test farmacia.tests_selenium
```

---

## 💡 Boas Práticas para Contribuir

- Sempre crie uma nova **branch** antes de fazer alterações:
  ```bash
  git checkout -b minha-feature
  ```
- Escreva mensagens de commit claras e descritivas.
- Rode os testes antes de abrir um Pull Request.
- Certifique-se de que o ambiente virtual está ativo durante o desenvolvimento.

---

