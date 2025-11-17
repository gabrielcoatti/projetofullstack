# 📊 Sistema de Gestão de Projetos

Sistema completo de gerenciamento de projetos com autenticação JWT, interface interativa e integrações com APIs externas.

## 🚀 Características Principais

### ✨ Funcionalidades
- ✅ **Autenticação completa** - Registro, login e JWT com expiração de 7 dias
- 📝 **CRUD de projetos** - Criar, editar, excluir e reordenar projetos
- 📌 **Sistema de fixação** - Fixe projetos importantes no topo da lista
- 🖼️ **Upload de imagens** - Anexe imagens aos projetos (qualquer formato, máx 5MB)
- 🔄 **Drag & Drop** - Reordene projetos arrastando (respeitando fixados/não-fixados)
- ✏️ **Edição inline** - Edite projetos diretamente na lista sem modal
- 🎯 **Prioridades** - Classifique projetos por prioridade (alta, média, baixa)
- 📊 **Estatísticas** - Visualize métricas sobre seus projetos
- 🌓 **Modo escuro/claro** - Interface adaptável com persistência de preferência
- 🏠 **Consulta de CEP** - Integração com API ViaCEP
- 💬 **Citações motivacionais** - Inspire-se com frases aleatórias
- 🔒 **Multi-usuário** - Cada usuário vê apenas seus próprios projetos

### 🎨 Interface
- Design moderno com gradientes e animações
- Responsiva para desktop e mobile
- Toast notifications para feedback ao usuário
- Modal para visualização de imagens em tela cheia

## 📦 Instalação

### Pré-requisitos
- Python 3.8 ou superior
- Navegador moderno (Chrome, Firefox, Edge, Safari)

### Passo a passo

1. **Clone o repositório**
```bash
git clone https://github.com/gabrielcoatti/projetofullstack.git
cd projetofullstack
```

2. **Instale as dependências Python**
```bash
pip install -r requirements.txt
```

3. **Inicie o servidor**
```bash
python basic_server.py
```

4. **Acesse no navegador**
```
http://localhost:8000
```

O sistema criará automaticamente o banco de dados SQLite na primeira execução.

## 🎯 Como usar

1. **Registro de conta**
   - Acesse a página inicial
   - Clique em "Registrar"
   - Preencha username, email e senha (mínimo 6 caracteres)

2. **Login**
   - Entre com suas credenciais
   - O token JWT é válido por 7 dias

3. **Gerenciar projetos**
   - **Adicionar**: Digite o título (mín. 5 caracteres), opcionalmente anexe uma imagem
   - **Editar**: Clique no botão ✏️ e edite diretamente na linha
   - **Fixar**: Clique em 📌 para fixar/desfixar projetos no topo
   - **Mover**: Use as setas ↑↓ ou arraste para reordenar
   - **Excluir**: Clique no botão 🗑️

4. **Funcionalidades extras**
   - Clique no botão ⚡ para acessar:
     - **Consultar CEP**: Busque endereços por CEP
     - **Citações**: Receba frases motivacionais
     - **Estatísticas**: Veja métricas dos seus projetos

5. **Modo escuro**
   - Clique no botão ☀️/🌙 para alternar temas
   - Sua preferência é salva automaticamente

## 📁 Estrutura do Projeto

```
projetofullstack/
├── basic_server.py          # Servidor backend Python com SQLite (625 linhas)
├── lista.html               # Aplicação principal SPA (1992 linhas)
├── index.html               # Redirecionamento automático para lista.html
├── style.css                # Estilos customizados com dark mode (143 linhas)
├── requirements.txt         # Dependências Python (PyJWT)
├── .gitignore               # Arquivos ignorados pelo Git
├── sistema_gestao.db        # Banco de dados SQLite (gerado automaticamente)
├── js/
│   └── auth.js             # Autenticação e utilitários (466 linhas)
│                            # - AuthManager: gerenciamento de tokens
│                            # - ApiClient: wrapper para requisições
│                            # - Validações e UI helpers
├── scripts/
│   └── clean_console.py    # Script para remoção de console.log
└── README.md               # Documentação completa (este arquivo)
```

## 🛠️ Tecnologias Utilizadas

### Backend
- **Python 3** - Linguagem base
- **SQLite** - Banco de dados embutido
- **PyJWT** - Autenticação via tokens JWT
- **HTTP Server** - Servidor HTTP nativo do Python

### Frontend
- **HTML5 / CSS3 / JavaScript ES6+** - Stack web moderno
- **Bootstrap 5** - Framework CSS para layout responsivo
- **Chart.js** - Biblioteca para gráficos
- **Fetch API** - Comunicação assíncrona com backend

### APIs Externas
- **ViaCEP** - Consulta de endereços por CEP
- **API de Citações** - Frases motivacionais (endpoint customizado)

## 🔐 Segurança

- ✅ **Senhas hasheadas com SHA256** - Armazenamento seguro no banco
- ✅ **Autenticação JWT** - Tokens com expiração de 7 dias
- ✅ **Rate Limiting** - Proteção contra brute force (5 tentativas/5min por IP)
- ✅ **CORS Restrito** - Apenas localhost autorizado (não `*`)
- ✅ **Validação Dupla** - Frontend + Backend (defense in depth)
- ✅ **Sanitização XSS** - Remove caracteres HTML perigosos (`<>"'`)
- ✅ **SQL Injection** - Queries parametrizadas (prepared statements)
- ✅ **Timeout Requests** - 10 segundos para prevenir travamentos
- ✅ **Validação de Tipos** - Apenas PNG, JPG, GIF, WebP permitidos
- ✅ **Limites de Tamanho** - 500 chars texto, 2MB imagens, 1000 chars descrição
- ✅ **Isolamento Multi-user** - `user_id` em todas as queries WHERE

## 📊 Endpoints da API

### Autenticação
```
POST /api/register    - Criar nova conta (validação email, username, senha)
POST /api/login       - Fazer login e receber JWT (rate limiting: 5 tentativas/5min)
```

### Projetos (requer autenticação JWT)
```
GET    /api/lists        - Listar todos os projetos do usuário (ordenados por pinned)
POST   /api/lists        - Criar novo projeto (validação: 3-500 chars, imagem max 2MB)
PUT    /api/lists/{id}   - Atualizar projeto específico (suporta order_index)
DELETE /api/lists/{id}   - Deletar projeto específico
DELETE /api/lists        - Deletar todos os projetos do usuário
```

### Funcionalidades Extras (requer autenticação)
```
GET /api/cep/{cep}     - Consultar CEP via ViaCEP (fallback em caso de erro)
GET /api/quotes        - Obter citação motivacional aleatória
```

**Total**: 9 endpoints RESTful completos

## 🐛 Troubleshooting

**Problema**: Servidor não inicia
- Verifique se a porta 8000 está disponível: `netstat -ano | findstr :8000`
- Certifique-se de ter instalado PyJWT: `pip install -r requirements.txt`
- No Linux/Mac, pode ser necessário: `python3 basic_server.py`

**Problema**: Login bloqueado após várias tentativas
- Rate limiting ativo: aguarde 5 minutos
- Alternativa: use o botão "Login Demo" para teste rápido

**Problema**: Login não funciona
- Limpe o cache do navegador (Ctrl+Shift+R)
- Verifique se o servidor está rodando em http://localhost:8000
- Confira o console do navegador (F12) para erros detalhados
- Verifique o terminal do servidor para logs de debug

**Problema**: Imagens não carregam
- Formatos suportados: PNG
- Tamanho máximo: 2MB (para melhor performance)
- Imagens são salvas como base64 no banco de dados
- Limpe o cache do navegador se necessário

**Problema**: Drag & Drop não funciona
- Projetos fixados (📌) não podem ser arrastados
- Não é possível mover entre zonas fixadas/não-fixadas
- Use as setas ↑↓ como alternativa

**Problema**: Mudanças não aparecem
- Force refresh: Ctrl+Shift+R (Windows) ou Cmd+Shift+R (Mac)
- Limpe o localStorage: F12 → Application → Local Storage → Clear All

## 📝 Banco de Dados

O sistema utiliza SQLite com as seguintes tabelas:

**users**
- id (INTEGER PRIMARY KEY)
- username (TEXT UNIQUE)
- email (TEXT UNIQUE)
- password (TEXT - SHA256)
- created_at (TIMESTAMP)

**projects**
- id (INTEGER PRIMARY KEY)
- user_id (INTEGER FK)
- texto (TEXT)
- description (TEXT)
- priority (TEXT)
- image_path (TEXT)
- pinned (INTEGER)
- order_index (INTEGER)
- created_at (TIMESTAMP)

## 📄 Licença

Este projeto é livre para uso educacional e pessoal.

## 👥 Equipe

- **Gabriel Coatti** - Backend & Infraestrutura
- **Gabriel Inácio** - Frontend & Interface
- **Fabricio Lucas** - Estilização & Integrações

---
