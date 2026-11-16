# EngSO Projeto M8 — Gerador de Relatórios com IA

Aplicação web desenvolvida em Flask para geração de relatórios acadêmicos e técnicos utilizando inteligência artificial, por meio da API Google Gemini.

## Funcionalidades

- Geração de relatórios personalizados com inteligência artificial.
- Seleção de diferentes perfis de usuário:
  - Aluno / Desenvolvedor
  - Professor / PO
  - Coordenador / Gestor do Projeto
- Geração de diferentes tipos de relatórios:
  - Técnico
  - Arquitetura
  - Progresso
  - Recomendações de estudo
- Envio de arquivos PDF, TXT e Markdown para análise.
- Visualização dos relatórios em HTML.
- Download dos relatórios no formato Markdown.
- Validação dos dados enviados e tratamento de erros.

## Tecnologias utilizadas

- Python 3.14
- Flask
- Google Gemini API
- Google GenAI SDK
- PyPDF
- Markdown
- Bleach
- Pytest
- Gunicorn
- Docker
- GitHub Actions
- Azure App Service

## Estrutura do projeto

```text
EngSO_Projeto-M8/
├── .github/
│   └── workflows/
│       └── main_engsoft-m8-proj-10419556.yml
├── static/
│   └── style.css
├── templates/
│   ├── index.html
│   └── resultado.html
├── .dockerignore
├── .gitignore
├── Dockerfile
├── app.py
├── requirements.txt
├── test_app.py
└── README.md
```

## Configuração do ambiente

### 1. Clonar o repositório

```bash
git clone https://github.com/Code016m/EngSO_Projeto-M8.git
cd EngSO_Projeto-M8
```

### 2. Criar o ambiente virtual

```bash
python -m venv .venv
```

Ativar no Windows:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Instalar as dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar a chave da API Gemini

Crie um arquivo `.env` na raiz do projeto:

```env
GEMINI_API_KEY=SUA_CHAVE_AQUI
```

Substitua `SUA_CHAVE_AQUI` pela chave válida da API Google Gemini.

**Importante:** não compartilhe nem envie o arquivo `.env` para o GitHub.

### 5. Executar a aplicação

```bash
python app.py
```

Acesse no navegador:

```text
http://127.0.0.1:5000
```

## Executar os testes

Para executar os testes automatizados:

```bash
pytest -v
```

Os testes verificam o carregamento das páginas, validação dos formulários, envio de arquivos, tratamento de erros, geração de relatórios e download dos resultados.

## Executar com Docker

### Criar a imagem

```bash
docker build -t engso-m8:1.1 .
```

### Executar o container

```bash
docker run --env-file .env -p 8000:8000 engso-m8:1.1
```

A aplicação ficará disponível em:

```text
http://localhost:8000
```

## Implantação

O projeto possui um workflow do GitHub Actions para automatizar a implantação no Azure App Service.

O processo utiliza o repositório GitHub e as credenciais configuradas nos Secrets do GitHub para autenticação e publicação.

A variável `GEMINI_API_KEY` deve ser configurada nas variáveis de ambiente da aplicação hospedada.

## Rotas principais

| Método | Rota | Descrição |
|---|---|---|
| GET | `/` | Exibe a página inicial |
| POST | `/gerar` | Processa os dados e gera o relatório |
| POST | `/baixar` | Disponibiliza o relatório em Markdown |

## Repositório

[GitHub — EngSO_Projeto-M8](https://github.com/Code016m/EngSO_Projeto-M8)