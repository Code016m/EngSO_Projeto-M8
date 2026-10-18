
import io
from types import SimpleNamespace

import pytest
import app as modulo

# Obtém a aplicação Flask que será testada
app = modulo.app


# Cria um cliente de testes para simular requisições à aplicação
@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.test_client() as cliente_teste:
        yield cliente_teste


# Prepara os dados padrão utilizados nos testes
def dados_formulario(**alteracoes):
    dados = {
        "perfil": "Aluno / Desenvolvedor",
        "tipo_relatorio": "tecnico",
        "dados": "Projeto de livraria desenvolvido em Python e Flask.",
        "solicitacao": "Explique as funcionalidades e sugira melhorias.",
    }

    # Permite modificar campos para testar diferentes situações
    dados.update(alteracoes)
    return dados


# Simula a resposta da inteligência artificial sem chamar a API real
def configurar_ia(
    monkeypatch,
    texto="## Relatório\nProjeto desenvolvido com Flask."
):
    def cliente_falso(api_key):
        return SimpleNamespace(
            models=SimpleNamespace(
                generate_content=lambda **kwargs: SimpleNamespace(
                    text=texto
                )
            )
        )

    # Configura uma chave fictícia e substitui o cliente real do Gemini
    monkeypatch.setenv("GEMINI_API_KEY", "chave_de_teste")
    monkeypatch.setattr(modulo.genai, "Client", cliente_falso)


# Testa se a página inicial é carregada corretamente
def test_pagina_inicial(client):
    resposta = client.get("/")

    assert resposta.status_code == 200
    assert b"Assistente" in resposta.data


# Testa a rejeição de um formulário completamente vazio
def test_formulario_vazio(client):
    resposta = client.post("/gerar", data={})

    assert resposta.status_code == 400
    assert b"Preencha todos os campos" in resposta.data


# Testa a validação individual dos campos obrigatórios
@pytest.mark.parametrize(
    "campo",
    ["perfil", "tipo_relatorio", "dados", "solicitacao"]
)
def test_formulario_parcial(client, campo):
    dados = dados_formulario()
    dados[campo] = ""

    resposta = client.post("/gerar", data=dados)

    assert resposta.status_code == 400
    assert b"Preencha todos os campos" in resposta.data


# Testa a rejeição de um perfil de usuário inexistente
def test_perfil_invalido(client):
    resposta = client.post(
        "/gerar",
        data=dados_formulario(perfil="Perfil inválido")
    )

    assert resposta.status_code == 400
    assert b"perfil de usu" in resposta.data


# Testa a rejeição de um tipo de relatório inválido
def test_tipo_relatorio_invalido(client):
    resposta = client.post(
        "/gerar",
        data=dados_formulario(tipo_relatorio="invalido")
    )

    assert resposta.status_code == 400
    assert b"tipo de relat" in resposta.data


# Testa a rejeição de arquivos com extensões não permitidas
def test_extensao_invalida(client):
    dados = dados_formulario()
    dados["arquivos"] = (
        io.BytesIO(b"Conteudo"),
        "projeto.exe"
    )

    resposta = client.post(
        "/gerar",
        data=dados,
        content_type="multipart/form-data"
    )

    assert resposta.status_code == 400
    assert b"formato inv" in resposta.data


# Testa a rejeição de arquivos TXT e Markdown sem conteúdo útil
@pytest.mark.parametrize("nome", ["projeto.txt", "projeto.md"])
def test_arquivo_vazio(client, nome):
    dados = dados_formulario()
    dados["arquivos"] = (
        io.BytesIO(b"   \n"),
        nome
    )

    resposta = client.post(
        "/gerar",
        data=dados,
        content_type="multipart/form-data"
    )

    assert resposta.status_code == 400
    assert b"texto" in resposta.data


# Testa o tratamento de um arquivo PDF inválido
def test_pdf_invalido(client):
    dados = dados_formulario()
    dados["arquivos"] = (
        io.BytesIO(b"Arquivo PDF invalido"),
        "projeto.pdf"
    )

    resposta = client.post(
        "/gerar",
        data=dados,
        content_type="multipart/form-data"
    )

    assert resposta.status_code == 400
    assert b"PDF" in resposta.data


# Testa a rejeição de arquivos maiores que o limite de 5 MB
def test_arquivo_maior_que_limite(client):
    dados = dados_formulario()
    dados["arquivos"] = (
        io.BytesIO(b"a" * (5 * 1024 * 1024 + 1)),
        "projeto.txt"
    )

    resposta = client.post(
        "/gerar",
        data=dados,
        content_type="multipart/form-data"
    )

    assert resposta.status_code == 400
    assert b"5 MB" in resposta.data


# Testa a rejeição de mais de três arquivos por solicitação
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
        content_type="multipart/form-data"
    )

    assert resposta.status_code == 400
    assert b"no m" in resposta.data


# Testa o comportamento quando a chave da API não está configurada
def test_chave_api_ausente(client, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    resposta = client.post(
        "/gerar",
        data=dados_formulario()
    )

    assert resposta.status_code == 500
    assert b"intelig" in resposta.data


# Testa o tratamento de erros durante a chamada à inteligência artificial
def test_falha_na_ia(client, monkeypatch):
    def cliente_com_erro(api_key):
        def gerar_conteudo(**kwargs):
            raise RuntimeError("Falha simulada")

        return SimpleNamespace(
            models=SimpleNamespace(
                generate_content=gerar_conteudo
            )
        )

    # Substitui o cliente real por um que simula uma falha
    monkeypatch.setenv("GEMINI_API_KEY", "chave_de_teste")
    monkeypatch.setattr(
        modulo.genai,
        "Client",
        cliente_com_erro
    )

    resposta = client.post(
        "/gerar",
        data=dados_formulario()
    )

    assert resposta.status_code == 503
    assert b"tente novamente" in resposta.data


# Testa o comportamento quando a IA retorna uma resposta vazia
def test_resposta_vazia_da_ia(client, monkeypatch):
    configurar_ia(monkeypatch, texto="")

    resposta = client.post(
        "/gerar",
        data=dados_formulario()
    )

    assert resposta.status_code == 502
    assert b"gerar o relat" in resposta.data


# Testa a geração e a apresentação de um relatório
def test_geracao_de_relatorio(client, monkeypatch):
    configurar_ia(monkeypatch)

    resposta = client.post(
        "/gerar",
        data=dados_formulario()
    )

    assert resposta.status_code == 200
    assert b"Relat" in resposta.data
    assert b"Projeto desenvolvido com Flask" in resposta.data
    assert b"Baixar relat" in resposta.data


# Testa se o HTML potencialmente perigoso é removido do relatório
def test_sanitizacao_do_relatorio(client, monkeypatch):
    configurar_ia(
        monkeypatch,
        texto='<script>alert("teste")</script>\nRelatório seguro.'
    )

    resposta = client.post(
        "/gerar",
        data=dados_formulario()
    )

    assert resposta.status_code == 200
    assert b"<script>" not in resposta.data
    assert b"Relat" in resposta.data


# Testa o download do relatório no formato Markdown
def test_download_relatorio(client):
    conteudo = (
        "# Relatório de teste\n\n"
        "Projeto desenvolvido com Flask."
    )

    resposta = client.post(
        "/baixar",
        data={"relatorio_markdown": conteudo}
    )

    assert resposta.status_code == 200
    assert "text/markdown" in resposta.content_type
    assert "relatorio.md" in resposta.headers["Content-Disposition"]
    assert resposta.data.decode("utf-8") == conteudo


# Testa a rejeição do download quando não há relatório
def test_download_vazio(client):
    resposta = client.post(
        "/baixar",
        data={"relatorio_markdown": ""}
    )

    assert resposta.status_code == 400


# Testa a geração de relatórios para todos os perfis disponíveis
@pytest.mark.parametrize(
    "perfil",
    [
        "Aluno / Desenvolvedor",
        "Professor / PO",
        "Coordenador / Gestor do Projeto",
    ]
)
def test_perfis_validos(client, monkeypatch, perfil):
    configurar_ia(monkeypatch)

    resposta = client.post(
        "/gerar",
        data=dados_formulario(perfil=perfil)
    )

    assert resposta.status_code == 200


# Testa todos os tipos de relatório disponíveis
@pytest.mark.parametrize(
    "tipo",
    ["tecnico", "arquitetura", "progresso", "estudo"]
)
def test_tipos_de_relatorio_validos(client, monkeypatch, tipo):
    configurar_ia(monkeypatch)

    resposta = client.post(
        "/gerar",
        data=dados_formulario(tipo_relatorio=tipo)
    )

    assert resposta.status_code == 200


# Testa o envio bem-sucedido de um arquivo TXT
def test_upload_txt_com_sucesso(client, monkeypatch):
    configurar_ia(monkeypatch)

    dados = dados_formulario()
    dados["arquivos"] = (
        io.BytesIO("Informação adicional.".encode("utf-8")),
        "dados.txt"
    )

    resposta = client.post(
        "/gerar",
        data=dados,
        content_type="multipart/form-data"
    )

    assert resposta.status_code == 200


# Testa se a validação das extensões ignora maiúsculas e minúsculas
def test_extensao_case_insensitive():
    assert modulo.extensao_permitida("PROJETO.PDF")
    assert modulo.extensao_permitida("notas.MD")
    assert not modulo.extensao_permitida("arquivo.exe")
    assert not modulo.extensao_permitida("")