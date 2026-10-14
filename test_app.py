# Importa as ferramentas de teste
import pytest

# Importa a aplicação Flask
from app import app

# Prepara a aplicação para executar os testes
@pytest.fixture
def client():
  # Ativa o modo de teste do Flask
  app.config["TESTING"] = True
  # Cria um cliente para simular requisições
  with app.test_client() as cliente_teste:
    yield cliente_teste

# Testa a página inicial abre corretamente
def test_pagina_inicial(client):
  resposta = client.get("/")
  # Verifica se a página foi carregada com sucesso (código 200)
  assert resposta.status_code == 200
  # Verifica se o título principal está presente
  assert b"Assistente de Relat" in resposta.data

# Testa se o sistema rejeita um formulário vazio
def test_formulario_vazio(client):
  resposta = client.post("/gerar", data={
    "perfil": "",
    "dados": "",
    "solicitacao": ""
  })
  # Espera o código HTTP 400, indicando dados inválidos
  assert resposta.status_code == 400
  # Verifica se a mensagem de validação foi exibida
  assert b"Preencha todos os campos" in resposta.data

# Testa se o sistema rejeita um formulário parcialmente preenchido
def test_formulario_parcial(client):
  resposta = client.post("/gerar", data={
    "perfil": "Aluno / Desenvolvedor",
    "dados": "Exemplo de dados",
    "solicitacao": ""
  })
  # Verifica se o sistema identificou o campo vazio
  assert resposta.status_code == 400
  # Verifica a mensagem de erro
  assert b"Preencha todos os campos" in resposta.data