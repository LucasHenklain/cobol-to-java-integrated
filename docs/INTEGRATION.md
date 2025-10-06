# Guia de Integração

Este documento descreve a integração entre o frontend React e o backend FastAPI do sistema Agent Crew para Migração COBOL para Java.

## Visão Geral da Integração

O sistema é composto por dois componentes principais:

1. **Backend (FastAPI/Python)**
   - API REST para gerenciamento de jobs
   - Agentes CrewAI para migração de código
   - Modelos de dados e serviços

2. **Frontend (React/TypeScript)**
   - Interface de usuário moderna com React e TypeScript
   - Design system com TailwindCSS e shadcn/ui
   - Páginas para gerenciamento de jobs, visualização de código e métricas

## Comunicação entre Frontend e Backend

### Serviço de API

O frontend se comunica com o backend através de um serviço de API implementado com Axios:

- **Arquivo**: `/frontend/src/services/api.ts`
- **Configuração**:
  ```typescript
  const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
    headers: {
      'Content-Type': 'application/json',
    },
  });
  ```

### Endpoints Principais

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/jobs` | GET | Listar jobs com paginação e filtros |
| `/api/jobs` | POST | Criar um novo job |
| `/api/jobs/{job_id}` | GET | Obter detalhes de um job específico |
| `/api/jobs/{job_id}/status` | GET | Obter status e progresso de um job |
| `/api/jobs/{job_id}/programs` | GET | Obter programas de um job |

### Configuração CORS

O backend está configurado para aceitar requisições do frontend:

```python
CORS_ORIGINS: List[str] = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://localhost:5173",  # Vite dev server
    "http://127.0.0.1:5173"   # Vite dev server alternative
]
```

## Componentes Integrados

### 1. Dashboard

O Dashboard exibe uma visão geral dos jobs de migração e métricas:

- **Arquivo**: `/frontend/src/pages/Dashboard.tsx`
- **Integração**:
  - Busca jobs usando React Query
  - Exibe estatísticas baseadas em dados reais
  - Atualização automática a cada 10 segundos

### 2. Formulário de Criação de Jobs

O formulário permite criar novos jobs de migração:

- **Arquivo**: `/frontend/src/pages/NewJob.tsx`
- **Integração**:
  - Envia dados do formulário para a API
  - Validação de campos
  - Feedback de sucesso/erro usando toast
  - Redirecionamento após criação bem-sucedida

### 3. Code Explorer

Permite visualizar e comparar código COBOL e Java:

- **Arquivo**: `/frontend/src/pages/CodeExplorer.tsx`
- **Integração**:
  - Busca programas de um job específico
  - Exibe código COBOL e Java lado a lado
  - Destaca diferenças e transformações

## Fluxo de Dados

1. **Criação de Job**:
   - Usuário preenche formulário no frontend
   - Frontend envia dados para `/api/jobs` via POST
   - Backend cria job e inicia agentes
   - Frontend redireciona para página de detalhes

2. **Monitoramento de Progresso**:
   - Dashboard busca jobs periodicamente
   - Frontend exibe progresso e status atual
   - Usuário pode navegar para detalhes de jobs específicos

3. **Exploração de Código**:
   - Usuário seleciona job no dashboard
   - Frontend busca programas do job
   - Usuário seleciona programa para visualizar
   - Frontend exibe código COBOL e Java lado a lado

## Configuração de Ambiente

### Variáveis de Ambiente do Frontend

Arquivo `.env` no diretório `/frontend`:

```
VITE_API_URL=http://localhost:8000
```

### Variáveis de Ambiente do Backend

Arquivo `.env` no diretório `/backend`:

```
DEBUG=True
HOST=0.0.0.0
PORT=8000
DATABASE_URL=sqlite:///./cobol_migration.db
OPENAI_API_KEY=sua_chave_api_aqui
OPENAI_MODEL=gpt-4.1-mini
```

## Solução de Problemas

### CORS Issues

Se o frontend não conseguir se comunicar com o backend devido a erros de CORS:

1. Verifique se o backend está configurado para aceitar requisições da origem do frontend
2. Certifique-se de que o frontend está enviando o cabeçalho `Origin` correto
3. Verifique se o backend está respondendo com os cabeçalhos CORS apropriados

### Erros de API

Se as chamadas de API estiverem falhando:

1. Verifique se o backend está em execução
2. Confirme se a URL da API no arquivo `.env` do frontend está correta
3. Verifique os logs do backend para mensagens de erro específicas
4. Use as ferramentas de desenvolvedor do navegador para inspecionar as requisições e respostas
