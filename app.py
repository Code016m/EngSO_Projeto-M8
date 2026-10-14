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

    # Obtém a chave da API do Gemini configurada no arquivo .env
    api_key = os.getenv("GEMINI_API_KEY")

    # Verifica se a chave da API foi configurada
    if not api_key or api_key == "SUA_CHAVE_AQUI":
      app.logger.error("A chave da API do Gemini não foi configurada.")
      return render_template(
        "index.html",
        erro="O serviço de inteligência artificial não está configurado."
      ), 500

    # Monta o prompt enviado para a inteligência artificial
    prompt = f"""
    Gere um relatório em português brasileiro sobre Engenharia de Software.
    Adapte o relatório ao perfil do usuário.
    Utilize somente as informações fornecidas, sem inventar dados.
    Organize o conteúdo usando títulos, subtítulos, listas e negrito em Markdown.
    Não utilize barras invertidas para escapar os símbolos de formatação.

    Perfil do usuário: {perfil}
    Dados do projeto: {dados}
    Solicitação: {solicitacao}
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

        # Verifica se a IA retornou conteúdo
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
        # Isso reduz o risco de inserir conteúdo HTML perigoso na página
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
      # Registra os detalhes técnicos no terminal
      app.logger.exception("Erro ao gerar relatório")
      
      # Mostra uma mensagem amigável na página inicial
      return render_template(
        "index.html",
        erro=(
          """
          O serviço de inteligência artificial está temporariamente indisponível. Aguarde alguns instantes e tente novamente.
          """
        )
      ), 503

# Inicia o servidor de desenvolvimento quando o arquivo é executado
if __name__ == "__main__":
    app.run(debug=True)
