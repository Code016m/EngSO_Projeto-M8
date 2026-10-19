# Utiliza Python como imagem base
FROM python:3.14-slim

# Define a pasta de trabalho dentro do container
WORKDIR /app

# Evita arquivos .pyc e mantém os logs visíveis
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copia e instala as dependências do projeto
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia os arquivos da aplicação para o container
COPY . .

# Informa a porta utilizada pela aplicação
EXPOSE 8000

# Inicia a aplicação Flask com Gunicorn
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-8000} app:app"]
