#!/bin/bash

# Script para iniciar o sistema de migração COBOL para Java
# Este script inicia tanto o backend quanto o frontend

echo "=== COBOL to Java Migration System ==="
echo "Starting backend and frontend services..."

# Verificar se os diretórios do projeto existem
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "Error: Project directories not found. Please make sure you're in the project root directory."
    exit 1
fi

# Função para iniciar o backend
start_backend() {
    echo "Starting backend service..."
    cd backend
    
    # Verificar se o ambiente virtual existe, se não, criar
    if [ ! -d "venv" ]; then
        echo "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Ativar ambiente virtual
    source venv/bin/activate
    
    # Instalar dependências
    echo "Installing backend dependencies..."
    pip install -r requirements.txt
    
    # Verificar se o arquivo .env existe
    if [ ! -f ".env" ]; then
        echo "Creating .env file from .env.example..."
        if [ -f ".env.example" ]; then
            cp .env.example .env
        else
            echo "DATABASE_URL=sqlite:///./cobol_migration.db" > .env
            echo "DEBUG=True" >> .env
            echo "HOST=0.0.0.0" >> .env
            echo "PORT=8000" >> .env
        fi
    fi
    
    # Iniciar o backend
    echo "Starting backend server at http://localhost:8000..."
    python main.py &
    BACKEND_PID=$!
    echo "Backend started with PID: $BACKEND_PID"
    
    # Voltar para o diretório raiz
    cd ..
}

# Função para iniciar o frontend
start_frontend() {
    echo "Starting frontend service..."
    cd frontend
    
    # Instalar dependências
    echo "Installing frontend dependencies..."
    npm install
    
    # Verificar se o arquivo .env existe
    if [ ! -f ".env" ]; then
        echo "Creating .env file..."
        echo "VITE_API_URL=http://localhost:8000" > .env
    fi
    
    # Iniciar o frontend
    echo "Starting frontend server at http://localhost:5173..."
    npm run dev &
    FRONTEND_PID=$!
    echo "Frontend started with PID: $FRONTEND_PID"
    
    # Voltar para o diretório raiz
    cd ..
}

# Função para limpar ao sair
cleanup() {
    echo "Stopping services..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
    fi
    echo "Services stopped."
    exit 0
}

# Registrar função de limpeza para sinais de interrupção
trap cleanup SIGINT SIGTERM

# Iniciar serviços
start_backend
sleep 5  # Aguardar o backend iniciar
start_frontend

echo ""
echo "=== System Started ==="
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo "Press Ctrl+C to stop all services"
echo ""

# Manter o script em execução
wait
