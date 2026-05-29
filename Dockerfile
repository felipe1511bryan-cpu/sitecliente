# Usa uma imagem oficial do Python mais leve baseada em Linux
FROM python:3.12-slim

# Instala as ferramentas de compilação em C++ dentro do Linux para o TgCrypto voar
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Define a pasta de trabalho dentro do servidor
WORKDIR /app

# Copia os arquivos do seu projeto para dentro do servidor
COPY . /app

# Instala as dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Comando que o servidor vai executar para ligar o robô automaticamente
CMD ["python", "motor_turbo.py"]