# Configuração de Variáveis de Ambiente para Google OAuth2

## Mudanças Implementadas

### ✅ Removido campo `expiry`
- O campo `expiry` foi removido do token OAuth2
- O Google agora gerencia automaticamente a expiração do token
- Tokens são renovados automaticamente quando necessário

### ✅ Uso de Variáveis de Ambiente
- As credenciais agora são lidas de variáveis de ambiente
- Não dependem mais dos arquivos `credentials.json` e `token.json`
- Mais seguro para deploy em produção

## Configuração

### 1. Configure as Variáveis de Ambiente

Execute o script de configuração para gerar os comandos:

```bash
python3 setup_env.py
```

### 2. Exporte as Variáveis

Copie e execute os comandos gerados:

```bash
# Credenciais OAuth2
export GOOGLE_CREDENTIALS_JSON='{"installed":{"client_id":"...","project_id":"..."}}'

# Token de acesso (sem campo expiry)
export GOOGLE_TOKEN_JSON='{"token":"...","refresh_token":"...","scopes":[...]}'
```

### 3. Para Uso Persistente

#### No ~/.bashrc ou ~/.zshrc:
```bash
echo 'export GOOGLE_CREDENTIALS_JSON="..."' >> ~/.zshrc
echo 'export GOOGLE_TOKEN_JSON="..."' >> ~/.zshrc
source ~/.zshrc
```

#### Em Docker:
```dockerfile
ENV GOOGLE_CREDENTIALS_JSON='{"installed":{"client_id":"..."}}'
ENV GOOGLE_TOKEN_JSON='{"token":"...","refresh_token":"..."}'
```

#### Em arquivo .env:
```bash
GOOGLE_CREDENTIALS_JSON={"installed":{"client_id":"..."}}
GOOGLE_TOKEN_JSON={"token":"...","refresh_token":"..."}
```

## Uso

### Validar Autenticação
```python
from src.auth import validate_authentication, check_oauth_info

# Mostrar informações das credenciais
check_oauth_info()

# Validar se a autenticação está funcionando
validate_authentication()
```

### Usar o Serviço Gmail
```python
from src.auth import get_gmail_service

service = get_gmail_service()
# Use o serviço normalmente
```

## Vantagens

### 🔒 Segurança
- Credenciais não ficam em arquivos no sistema
- Mais fácil de gerenciar em ambientes de produção
- Reduz riscos de commit acidental de credenciais

### 🚀 Deploy
- Funciona melhor com containers
- Integração mais fácil com CI/CD
- Configuração por ambiente (dev, staging, prod)

### 🛠️ Manutenção
- Google gerencia automaticamente a expiração
- Menos campos para rastrear manualmente
- Renovação automática de tokens

## Troubleshooting

### ❌ Erro: Variável não encontrada
```bash
# Verificar se as variáveis estão configuradas
echo $GOOGLE_CREDENTIALS_JSON
echo $GOOGLE_TOKEN_JSON
```

### ❌ Erro: JSON mal formado
```bash
# Verificar sintaxe JSON
python3 -c "import json, os; json.loads(os.environ['GOOGLE_CREDENTIALS_JSON'])"
```

### ❌ Token expirado
O sistema agora renova automaticamente. Se houver problemas:
```python
from src.auth import reset_authentication
reset_authentication()
```

## Migração dos Arquivos

Os arquivos `credentials.json` e `token.json` ainda existem mas não são mais usados pelo código atualizado. Você pode mantê-los como backup ou removê-los após confirmar que tudo funciona com as variáveis de ambiente.
