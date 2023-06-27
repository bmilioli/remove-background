# Usa uma imagem base com o Python instalado
FROM python:3.10-slim

# Define o diretório de trabalho
WORKDIR /app

# Copia o arquivo requirements.txt para o diretório de trabalho
COPY requirements.txt .

# Copia o arquivo .env para o diretório de trabalho
COPY .env .

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código do aplicativo para o diretório de trabalho
COPY . .

# Define a porta que o aplicativo será exposto
EXPOSE 8000

# Comando para executar o aplicativo
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
