# 📧 Sistema de Scraping de Emails Gmail

Sistema automatizado para extrair emails com anexos do Gmail usando a API oficial do Google.

## 🚀 Funcionalidades

1. **Autenticação via Service Account** - Usa conta de serviço com delegação de domínio
2. **Busca por Label** - Filtra emails pelo label "DOC-MEDICOS"
3. **Extração Completa** - Extrai remetente, assunto, corpo e anexos
4. **Download de Anexos** - Organiza anexos por pasta do remetente
5. **Saída JSON** - Gera arquivo JSON estruturado com todos os dados

## 📁 Estrutura do Projeto

```
scrape-data/
├── src/
│   ├── auth.py           # Autenticação Gmail API
│   ├── gmail_client.py   # Operações na caixa de e-mail
│   ├── drive_client.py   # Upload/geração de link (futuro)
│   ├── models.py         # Dataclasses e tipos
│   ├── pipeline.py       # Orquestração de ponta a ponta
│   └── utils.py          # Utilitários
├── tests/                # Testes (futuro)
├── anexos-email/         # Pasta para anexos baixados
├── requirements.txt      # Dependências Python
├── .env.example          # Exemplo de variáveis de ambiente
└── README.md
```

## 🔧 Configuração

### 1. Dependências

```bash
# Ativar ambiente virtual
source .venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### 2. Configuração OAuth2

1. Coloque o arquivo `credentials.json` na raiz do projeto (já está presente)
2. Configure as variáveis no arquivo `.env` (copie de `.env.example`)

### 3. Variáveis de Ambiente

```bash
cp .env.example .env
```

Edite o `.env`:
```
CREDENTIALS_FILE=credentials.json
TOKEN_FILE=token.json
LABEL_NAME=DOC-MEDICOS
DEBUG=false
```

### 4. Primeira Autenticação

```bash
# Teste de autenticação (uma janela do navegador será aberta)
python test_oauth.py

# Para resetar a autenticação
python test_oauth.py --reset
```

## 📖 Como Usar

### Uso Básico

```python
from src.pipeline import EmailScrapingPipeline

# Criar pipeline
pipeline = EmailScrapingPipeline()

# Executar scraping completo
success = pipeline.run_full_pipeline(
    label_name="DOC-MEDICOS",
    max_emails=50,
    output_file="emails_data.json"
)

if success:
    pipeline.print_summary()
```

### Uso via Linha de Comando

```bash
# Executar pipeline
python -m src.pipeline --label "DOC-MEDICOS" --max-emails 100 --output results.json

# Teste básico
python test_pipeline.py

# Exemplo de uso
python example_usage.py
```

### Uso Avançado

```python
from src.gmail_client import GmailClient

# Cliente direto
client = GmailClient()

# Listar mensagens
message_ids = client.list_messages_by_label("DOC-MEDICOS", max_results=10)

# Processar mensagem específica
for message_id in message_ids:
    email_data = client.get_message_details(message_id)
    print(f"Email de: {email_data.from_email}")
    print(f"Anexos: {len(email_data.attachments)}")
```

## 📄 Formato de Saída

O sistema gera um arquivo JSON com a seguinte estrutura:

```json
{
  "metadata": {
    "total_emails": 5,
    "processed_at": "2025-08-30T14:30:00",
    "label_used": "DOC-MEDICOS"
  },
  "emails": [
    {
      "from": "exemplo@hospital.com",
      "subject": "Ficha cadastral",
      "body": "Conteúdo do email em texto plano...",
      "attachments": [
        {
          "filename": "ficha.pdf",
          "mimeType": "application/pdf",
          "anexoPath": "anexos-email/exemplo/ficha.pdf"
        }
      ]
    }
  ]
}
```

## 📁 Organização de Anexos

Os anexos são organizados por remetente:

```
anexos-email/
├── thai.vaz/           # thai.vaz@hotmail.com
│   ├── documento1.pdf
│   └── planilha.xlsx
├── medico.silva/       # medico.silva@hospital.com
│   └── receita.jpg
└── admin/              # admin@clinica.com.br
    ├── relatorio.docx
    └── dados.csv
```

## 🧪 Testes

```bash
# Teste básico de funcionamento
python test_pipeline.py

# Teste de autenticação
python -c "from src.auth import validate_authentication; print(validate_authentication())"
```

## 🔍 Troubleshooting

### Problemas Comuns

1. **Erro de Autenticação**
   - Verifique se o arquivo JSON da service account está correto
   - Confirme se a delegação de domínio está configurada
   - Teste com `validate_authentication()`

2. **Label não encontrado**
   - Verifique se o label "DOC-MEDICOS" existe no Gmail
   - Use `client.labels` para ver todos os labels disponíveis

3. **Erro de Permissões**
   - Confirme os scopes no service account
   - Verifique se a conta tem acesso ao email delegado

### Debug

Ative o modo debug no `.env`:
```
DEBUG=true
```

## 📋 Roadmap

- [ ] Implementar cliente Google Drive
- [ ] Adicionar filtros por data
- [ ] Implementar retry automático
- [ ] Adicionar testes unitários
- [ ] Melhorar logging
- [ ] Interface web (opcional)

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request
