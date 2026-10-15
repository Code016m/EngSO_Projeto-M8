# Importa ferramentas de teste e manipulação de arquivos
import io
from types import SimpleNamespace

import pytest
import app as modulo

# Obtém a aplicação Flask
app = modulo.app

# Prepara a aplicação para executar os testes
@pytest.fixture
def client():
  app.config["TESTING"] = True
  with app.test_client() as cliente_teste:
    yield cliente_teste

# Cria dados válidos para reutilizar nos testes
def dados_formulario(**alteracoes):
  dados = {
    "perfil": "Aluno / Desenvolvedor",
    "tipo_relatorio": "tecnico",
    "dados": "Projeto de livraria desenvolvido em Python e Flask.",
    "solicitacao": "Explique as funcionalidades e sugira melhorias.",
  }
  dados.update(alteracoes)
  return dados

# Simula uma resposta da inteligência artificial
def configurar_ia(monkeypatch, texto="## Relatório\nProjeto desenvolvido com Flask."):
  def cliente_falso(api_key):
    return SimpleNamespace(
      models=SimpleNamespace(
      generate_content=lambda **kwargs: SimpleNamespace(text=texto)
    )
  )
  monkeypatch.setenv("GEMINI_API_KEY", "chave_de_teste")
  monkeypatch.setattr(modulo.genai, "Client", cliente_falso)

# Testa se a página inicial abre corretamente
def test_pagina_inicial(client):
  resposta = client.get("/")
  
  assert resposta.status_code == 200
  assert b"Assistente" in resposta.data

# Testa se o sistema rejeita um formulário vazio
def test_formulario_vazio(client):
  resposta = client.post("/gerar", data={})
  
  assert resposta.status_code == 400
  assert b"Preencha todos os campos" in resposta.data


# Testa se o sistema rejeita campos obrigatórios vazios
@pytest.mark.parametrize(
  "campo",
  ["perfil", "tipo_relatorio", "dados", "solicitacao"],
)
def test_formulario_parcial(client, campo):
  dados = dados_formulario()
  dados[campo] = ""

  resposta = client.post("/gerar", data=dados)

  assert resposta.status_code == 400
  assert b"Preencha todos os campos" in resposta.data

# Testa se o sistema rejeita um perfil inválido
def test_perfil_invalido(client):
  resposta = client.post("/gerar", data=dados_formulario(perfil="Perfil inválido"))

  assert resposta.status_code == 400
  assert b"perfil de usu" in resposta.data

# Testa se o sistema rejeita um tipo de relatório inválido
def test_tipo_relatorio_invalido(client):
  resposta = client.post(
    "/gerar",
    data=dados_formulario(tipo_relatorio="invalido"),
  )

  assert resposta.status_code == 400
  assert b"tipo de relat" in resposta.data

# Testa se o sistema rejeita arquivos com formatos não permitidos
def test_extensao_invalida(client):
  dados = dados_formulario()
  dados["arquivos"] = (io.BytesIO(b"Conteudo"), "projeto.exe")

  resposta = client.post(
    "/gerar",
    data=dados,
    content_type="multipart/form-data",
  )

  assert resposta.status_code == 400
  assert b"formato inv" in resposta.data


# Testa se arquivos TXT e MD vazios são rejeitados
@pytest.mark.parametrize("nome", ["projeto.txt", "projeto.md"])
def test_arquivo_vazio(client, nome):
  dados = dados_formulario()
  dados["arquivos"] = (io.BytesIO(b"   \n"), nome)

  resposta = client.post(
    "/gerar",
    data=dados,
    content_type="multipart/form-data",
  )

  assert resposta.status_code == 400
  assert b"texto" in resposta.data


# Testa se um PDF inválido é rejeitado
def test_pdf_invalido(client):
  dados = dados_formulario()
  dados["arquivos"] = (io.BytesIO(b"Arquivo PDF invalido"), "projeto.pdf")

  resposta = client.post(
    "/gerar",
    data=dados,
    content_type="multipart/form-data",
  )

  assert resposta.status_code == 400
  assert b"PDF" in resposta.data


# Testa se arquivos maiores que 5 MB são rejeitados
def test_arquivo_maior_que_limite(client):
  conteudo = b"a" * (5 * 1024 * 1024 + 1)
  dados = dados_formulario()
  dados["arquivos"] = (io.BytesIO(conteudo), "projeto.txt")

  resposta = client.post(
    "/gerar",
    data=dados,
    content_type="multipart/form-data",
  )

  assert resposta.status_code == 400
  assert b"5 MB" in resposta.data


# Testa se o sistema rejeita mais de três arquivos
def test_quantidade_excessiva_de_arquivos(client):
  dados = dados_formulario()
  dados["arquivos"] = [
    (io.BytesIO(b"Conteudo A"), "a.txt"),
    (io.BytesIO(b"Conteudo B"), "b.txt"),
    (io.BytesIO(b"Conteudo C"), "c.txt"),
    (io.BytesIO(b"Conteudo D"), "d.txt"),
  ]

  resposta = client.post(
    "/gerar",
    data=dados,
    content_type="multipart/form-data",
  )

  assert resposta.status_code == 400
  assert b"no m" in resposta.data


# Testa o comportamento quando a chave da API não está configurada
def test_chave_api_ausente(client, monkeypatch):
  monkeypatch.delenv("GEMINI_API_KEY", raising=False)

  resposta = client.post(
    "/gerar",
    data=dados_formulario(),
  )

  assert resposta.status_code == 500
  assert b"intelig" in resposta.data


# Testa o tratamento de falhas na comunicação com a IA
def test_falha_na_ia(client, monkeypatch):
  def cliente_com_erro(api_key):
    def gerar_conteudo(**kwargs):
      raise RuntimeError("Falha simulada")

    return SimpleNamespace(
      models=SimpleNamespace(generate_content=gerar_conteudo)
    )

  monkeypatch.setenv("GEMINI_API_KEY", "chave_de_teste")
  monkeypatch.setattr(modulo.genai, "Client", cliente_com_erro)

  resposta = client.post(
    "/gerar",
    data=dados_formulario(),
  )

  assert resposta.status_code == 503
  assert b"tente novamente" in resposta.data


# Testa se o sistema trata uma resposta vazia da IA
def test_resposta_vazia_da_ia(client, monkeypatch):
  configurar_ia(monkeypatch, texto="")

  resposta = client.post(
    "/gerar",
    data=dados_formulario(),
  )

  assert resposta.status_code == 502
  assert b"gerar o relat" in resposta.data


# Testa a geração de um relatório com dados válidos
def test_geracao_de_relatorio(client, monkeypatch):
  configurar_ia(monkeypatch)

  resposta = client.post(
    "/gerar",
    data=dados_formulario(),
  )

  assert resposta.status_code == 200
  assert b"Relat" in resposta.data
  assert b"Projeto desenvolvido com Flask" in resposta.data
  assert b"Baixar relat" in resposta.data


# Testa se códigos HTML perigosos são removidos do relatório
def test_sanitizacao_do_relatorio(client, monkeypatch):
  configurar_ia(
    monkeypatch,
    texto='<script>alert("teste")</script>\nRelatório seguro.',
  )

  resposta = client.post(
    "/gerar",
    data=dados_formulario(),
  )

  assert resposta.status_code == 200
  assert b"<script>" not in resposta.data
  assert b"Relat" in resposta.data


# Testa se o relatório pode ser baixado em Markdown
def test_download_relatorio(client):
  conteudo = "# Relatório de teste\n\nProjeto desenvolvido com Flask."

  resposta = client.post(
    "/baixar",
    data={"relatorio_markdown": conteudo},
  )

  assert resposta.status_code == 200
  assert "text/markdown" in resposta.content_type
  assert "relatorio.md" in resposta.headers["Content-Disposition"]
  assert resposta.data.decode("utf-8") == conteudo


# Testa se o sistema impede o download de um relatório vazio
def test_download_vazio(client):
  resposta = client.post(
    "/baixar",
    data={"relatorio_markdown": ""},
  )

  assert resposta.status_code == 400


# Testa se todos os perfis válidos são aceitos
@pytest.mark.parametrize(
  "perfil",
  [
    "Aluno / Desenvolvedor",
    "Professor / PO",
    "Coordenador / Gestor do Projeto",
  ],
)
def test_perfis_validos(client, monkeypatch, perfil):
  configurar_ia(monkeypatch)

  resposta = client.post(
    "/gerar",
    data=dados_formulario(perfil=perfil),
  )

  assert resposta.status_code == 200

# Testa se todos os tipos de relatório são aceitos
@pytest.mark.parametrize(
  "tipo",
  ["tecnico", "arquitetura", "progresso", "estudo"],
)

def test_tipos_de_relatorio_validos(client, monkeypatch, tipo):
  configurar_ia(monkeypatch)

  resposta = client.post(
    "/gerar",
    data=dados_formulario(tipo_relatorio=tipo),
  )

  assert resposta.status_code == 200
