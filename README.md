# Agent Crew para Migração COBOL para Java

Sistema de migração automatizada de código COBOL para Java utilizando agentes de IA orquestrados por CrewAI.

## 🎯 Visão Geral

Este projeto implementa um sistema multi-agente inteligente para automatizar a migração de sistemas legados COBOL para Java, reduzindo significativamente o esforço manual e aumentando a precisão da conversão.

## 🏗️ Arquitetura

O sistema é composto por três camadas principais:

### 1. Frontend (React/TypeScript)
- Dashboard de gerenciamento de jobs
- Visualizador de código side-by-side (COBOL ↔ Java)
- Interface de revisão humana
- Métricas e logs em tempo real

### 2. Backend (FastAPI/Python)
- API REST para gerenciamento de jobs
- Orquestração de agentes via CrewAI
- Persistência de dados (SQLite/PostgreSQL)
- Processamento assíncrono

### 3. Agentes de IA (CrewAI)
- **InventoryAgent**: Escaneia repositórios COBOL
- **COBOLParserAgent**: Analisa e gera AST
- **TranslatorAgent**: Converte lógica COBOL → Java
- **TestGeneratorAgent**: Gera testes automatizados
- **ValidatorAgent**: Valida resultados

## 🚀 Inicialização Rápida

### Método Simples (Script Automatizado)

Para iniciar todo o sistema com um único comando:

```bash
./start.sh
```

Este script:
- Inicia o backend na porta 8000
- Inicia o frontend na porta 5173
- Configura automaticamente os arquivos .env necessários
- Instala as dependências necessárias

### Método Manual

#### 1. Configurar e Iniciar o Backend

```bash
# Navegar para o diretório do backend
cd backend

# Criar ambiente virtual Python (se não existir)
python3 -m venv venv

# Ativar ambiente virtual
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente (se necessário)
cp .env.example .env
# Editar .env conforme necessário

# Iniciar o servidor
python main.py
```

O backend estará disponível em `http://localhost:8000`.

#### 2. Configurar e Iniciar o Frontend

```bash
# Navegar para o diretório do frontend
cd frontend

# Instalar dependências
npm install

# Configurar variáveis de ambiente
echo "VITE_API_URL=http://localhost:8000" > .env

# Iniciar o servidor de desenvolvimento
npm run dev
```

O frontend estará disponível em `http://localhost:5173`.

## 📋 Funcionalidades

### Funcionalidades Principais

- ✅ Dashboard com overview de jobs e métricas
- ✅ Criação de jobs de migração
- ✅ Code explorer com diff viewer COBOL ↔ Java
- ✅ Fila de revisão com aprovações
- ✅ Visualização de resultados de testes
- ✅ Sistema de navegação intuitivo

### Design System

- Paleta técnica: azuis profundos, roxos para highlights, verde/vermelho para status
- Tipografia clara e legível
- Animações sutis para feedback
- Dark mode por padrão (ambiente de desenvolvimento)
- Componentes modulares e reutilizáveis

## 🎨 Stack Tecnológico

### Backend
- FastAPI (Python 3.11)
- CrewAI
- SQLAlchemy
- SQLite/PostgreSQL

### Frontend
- React 18
- TypeScript
- TailwindCSS
- shadcn/ui
- React Query

### Agentes & Tools
- OpenAI API
- Axios
- Chart.js

## 📊 Métricas de Sucesso

- **Taxa de conversão automática**: % de código convertido sem intervenção
- **Taxa de sucesso de testes**: % de testes passando
- **Tempo de primeira compilação**: Tempo até código Java compilar
- **Linhas de código processadas**: Volume migrado
- **Revisões humanas**: Quantidade de intervenções

## 🧪 Testes

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

## 📖 Documentação

- [Guia de Integração](docs/INTEGRATION.md)
- [Arquitetura Detalhada](docs/ARCHITECTURE.md)
- [Guia de Desenvolvimento](docs/DEVELOPMENT.md)
- [API Reference](docs/API.md)

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 👥 Time

Desenvolvido para o Challenge FIAP - Ford
