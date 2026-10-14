
import os
from flask import Flask, render_template, request
from dotenv import load_dotenv
from google import genai

# Carrega as configurações do arquivo .env
load_dotenv()

# Configura o Flask
app = Flask(__name__)


# Abre a página inicial
@app.route("/")
def index():
    return render_template("index.html")


# Recebe os dados do formulário e gera o relatório
@app.route("/gerar", methods=["POST"])
def gerar_relatorio():

    # Obtém os dados preenchidos pelo usuário
    perfil = request.form.get("perfil", "").strip()
    dados = request.form.get("dados", "").strip()
    solicitacao = request.form.get("solicitacao", "").strip()

    # Verifica se todos os campos foram preenchidos
    if not perfil or not dados or not solicitacao:
        return "Preencha todos os campos do formulário.", 400

    # Obtém a chave da API do Gemini
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key or api_key == "SUA_CHAVE_AQUI":
        return "Configure a chave da API no arquivo .env.", 500

    # Monta as instruções para a inteligência artificial
    prompt = f"""
    Gere um relatório em português brasileiro sobre Engenharia de Software.
    Adapte o relatório ao perfil do usuário.
    Utilize somente as informações fornecidas, sem inventar dados.

    Perfil: {perfil}
    Dados do projeto: {dados}
    Solicitação: {solicitacao}
    """

    try:
        # Conecta à API e solicita a geração do relatório
        cliente = genai.Client(api_key=api_key)
        resposta = cliente.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        # Obtém o texto gerado pela IA
        relatorio = resposta.text or "Nenhum relatório foi gerado."

        # Exibe o relatório na página
        return f"<h1>Relatório gerado</h1><pre>{relatorio}</pre><a href='/'>Voltar</a>"

    except Exception:
        # Registra o erro no terminal para facilitar a correção
        app.logger.exception("Erro ao gerar relatório")
        return "Erro ao gerar o relatório. Verifique a API e a conexão.", 500


# Inicia o servidor local
if __name__ == "__main__":
    app.run(debug=True)
