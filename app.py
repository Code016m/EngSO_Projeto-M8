import os
import markdown
import bleach

from flask import Flask, render_template, request
from dotenv import load_dotenv
from google import genai

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Cria a aplicação Flask
app = Flask(__name__)


# Abre a página inicial do sistema
@app.route("/")
def index():
    return render_template("index.html")


# Recebe os dados do formulário e gera o relatório
@app.route("/gerar", methods=["POST"])
def gerar_relatorio():

    # Obtém os valores preenchidos no formulário
    perfil = request.form.get("perfil", "").strip()
    dados = request.form.get("dados", "").strip()
    solicitacao = request.form.get("solicitacao", "").strip()

    # Verifica se todos os campos obrigatórios foram preenchidos
    if not perfil or not dados or not solicitacao:
      # Retorna à página inicial mostrando uma mensagem de erro
      return render_template(
        "index.html",
        erro="Preencha todos os campos antes de gerar o relatório."
      ), 400

    # Define as instruções específicas de cada perfil
    instrucoes_perfil = {
      "Aluno / Desenvolvedor": """
        Priorize os aspectos técnicos do projeto.
        Explique funcionalidades, implementação e decisões técnicas.
        Identifique dificuldades ou lacunas presentes nos dados.
        Sugira assuntos para estudo relacionados ao projeto.
        Utilize uma linguagem didática e acessível.
      """,

      "Professor / PO": """
        Priorize o acompanhamento e a avaliação do projeto.
        Organize requisitos, funcionalidades, entregas e progresso informado.
        Destaque pendências e critérios de aceitação relevantes.
        Aponte itens que precisam de validação ou acompanhamento.
        Utilize uma linguagem objetiva e profissional.
      """,

      "Coordenador / Gestor do Projeto": """
        Priorize a visão geral da evolução do projeto.
        Consolide resultados, atividades e situação das entregas informadas.
        Identifique riscos, dependências e possíveis atrasos somente quando houver evidências nos dados fornecidos.
        Apresente prioridades e recomendações para apoiar decisões.
        Utilize uma linguagem executiva, clara e objetiva.
      """,
    }

    # Verifica se o perfil selecionado é válido
    if perfil not in instrucoes_perfil:
      return render_template(
        "index.html", erro="Selecione um perfil de usuário válido."
      ), 400

    # Obtém a chave da API do Gemini configurada no arquivo .env
    api_key = os.getenv("GEMINI_API_KEY")

    # Verifica se a chave da API foi configurada
    if not api_key or api_key == "SUA_CHAVE_AQUI":
      app.logger.error("A chave da API do Gemini não foi configurada.")

      return render_template(
        "index.html",
        erro="O serviço de inteligência artificial não está configurado."
      ), 500

    # Monta as instruções completas enviadas à inteligência artificial
    prompt = f"""
      Você é um assistente de Engenharia de Software que gera relatórios
      a partir dos dados de um projeto.

      REGRAS GERAIS:
      - Escreva em português brasileiro.
      - Utilize somente informações fornecidas pelo usuário.
      - Não invente atividades, resultados, datas, métricas ou riscos.
      - Quando faltarem informações, indique que não foram fornecidas.
      - Adapte o conteúdo ao perfil selecionado.
      - Organize o relatório com títulos, subtítulos e listas em Markdown.
      - Atenda também à solicitação específica do usuário.
      
      PERFIL DO USUÁRIO: {perfil}
      INSTRUÇÕES ESPECÍFICAS DO PERFIL: {instrucoes_perfil[perfil]}
      DADOS DO PROJETO: {dados}
      SOLICITAÇÃO DO USUÁRIO: {solicitacao}
    """

    try:
        # Cria o cliente para acessar a API do Gemini
        cliente = genai.Client(api_key=api_key)

        # Solicita à IA a geração do relatório
        resposta = cliente.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt
        )

        # Obtém o texto gerado pela IA
        relatorio = resposta.text or ""

        # Verifica se a IA retornou algum conteúdo
        if not relatorio.strip():
          app.logger.warning("A IA não retornou conteúdo para o relatório.")
          return render_template(
            "index.html",
            erro="Não foi possível gerar o relatório. Tente novamente."
          ), 502

        # Corrige possíveis barras invertidas nos marcadores Markdown
        relatorio = (
            relatorio
            .replace(r"\#", "#")
            .replace(r"\*", "*")
            .replace(r"\-", "-")
        )

        # Converte o Markdown gerado em HTML
        html_relatorio = markdown.markdown(
            relatorio,
            extensions=["extra"]
        )

        # Permite somente as tags HTML necessárias para o relatório
        # Limita a exibição de conteúdo potencialmente malicioso
        html_relatorio = bleach.clean(
            html_relatorio,
            tags=[
                "h1", "h2", "h3", "h4",
                "p", "strong", "em", "ul", "ol", "li",
                "blockquote", "pre", "code", "hr"
            ],
            attributes={},
            strip=True
        )

        # Exibe o relatório formatado na página de resultado
        return render_template("resultado.html", relatorio=html_relatorio)

    except Exception:
      # Registra detalhes técnicos do erro no terminal
      app.logger.exception("Erro ao gerar relatório")
      # Exibe uma mensagem amigável caso a IA esteja indisponível
      return render_template(
        "index.html",
        erro=(
          "Não foi possível gerar o relatório neste momento. "
          "Verifique a conexão e tente novamente."
        )
      ), 503

# Inicia o servidor de desenvolvimento
if __name__ == "__main__":
    app.run(debug=True)
