# Sistema de Scraping e Classificação de Documentos Médicos

Sistema completo para extração e classificação automática de documentos médicos de emails Gmail, utilizando Google Cloud Vision API para inferir tipos de documentos.

## 🚀 Funcionalidades

### 📧 Scraping de Emails
- Extração automática de emails do Gmail via API
- Download de anexos (imagens e PDFs)
- Filtragem por labels
- Metadados detalhados de cada email

### 🔍 Classificação de Documentos
- **Classificação automática** de 20 tipos de documentos médicos
- **Google Cloud Vision API** para OCR e análise de imagem
- **Modo de teste** sem necessidade de configurar API
- **Heurísticas inteligentes** baseadas em palavras-chave

### 📊 Tipos de Documentos Suportados

| Tipo | Descrição | Estratégia de Detecção |
|------|-----------|----------------------|
| 📸 `FOTO_3X4` | Fotos 3x4 para documentos | Regex filename + detecção de rosto |
| 🆔 `RG` | Registro Geral/Identidade | Palavras-chave + padrões |
| 📄 `CPF` | Cadastro Pessoa Física | Regex CPF + palavras-chave |
| 🏥 `CARTAO_SUS` | Cartão Nacional de Saúde | Palavras-chave SUS/CNS |
| 👨‍⚕️ `CRM` | Conselho Regional Medicina | Palavras-chave CRM |
| 🚗 `CNH` | Carteira Nacional Habilitação | Palavras-chave CNH/DETRAN |
| 🏠 `COMPROVANTE_ENDERECO` | Comprovante residência | Empresas locais + palavras-chave |
| 🎓 `DIPLOMA_MEDICINA` | Diploma graduação | Diploma + Medicina |
| 🚑 `CERTIFICADO_ACLS` | Certificação ACLS | Palavras-chave ACLS |
| 🚨 `CERTIFICADO_ATLS` | Certificação ATLS | Palavras-chave ATLS |
| 👶 `CERTIFICADO_PALS` | Certificação PALS | Palavras-chave PALS |
| 🏆 `CERTIFICADO_ESPECIALIDADE` | Certificados especialidade | Especialidade + certificado |
| 📚 `CERTIFICADO_POS_GRADUACAO` | Certificados pós-graduação | Pós-graduação + certificado |
| 📝 `CURRICULO` | Currículos | Palavras-chave currículo |
| ⚠️ `REVISAO_MANUAL` | Necessita revisão | Fallback para não identificados |

## 📁 Estrutura do Projeto

```
scrape-data/
├── src/                          # Código fonte principal
│   ├── auth.py                   # Autenticação Gmail
│   ├── gmail_client.py          # Cliente Gmail API
│   ├── models.py                # Modelos de dados
│   ├── utils.py                 # Utilitários
│   ├── pipeline.py              # Pipeline principal
│   └── document_classifier.py   # Classificador de documentos
├── anexos-email/                # Anexos baixados
├── emails_data.json            # Dados extraídos dos emails
├── emails.json                 # Dados com classificações
├── classify_documents.py       # Script standalone de classificação
├── generate_report.py          # Gerador de relatórios
├── requirements.txt            # Dependências Python
└── credentials.json           # Credenciais OAuth Gmail
```

## 🛠️ Instalação e Configuração

### 1. Configuração do Ambiente
```bash
# Clone o repositório
cd scrape-data

# Crie ambiente virtual
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# ou
.venv\Scripts\activate     # Windows

# Instale dependências
pip install -r requirements.txt
```

### 2. Configuração Gmail API
1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie projeto e ative Gmail API
3. Configure OAuth 2.0 e baixe `credentials.json`
4. Execute `python setup_env.py` para autorizar

### 3. Configuração Google Cloud Vision (Opcional)
Para classificação com IA real:
1. Ative Vision API no mesmo projeto
2. Crie service account e baixe credenciais
3. Salve como `google_cloud_credentials.json`

## 🎯 Como Usar

### Classificação Rápida (Modo Teste)
```bash
# Classifica documentos sem usar API
python classify_documents.py --test-mode

# Gera relatório
python generate_report.py
```

### Classificação Completa (Com API)
```bash
# Classifica usando Google Cloud Vision API
python classify_documents.py --input emails_data.json --output emails_classified.json

# Gera relatório detalhado
python generate_report.py --file emails_classified.json
```

### Pipeline Completo
```bash
# Scraping + Classificação
python src/pipeline.py --max-emails 100 --classify

# Apenas scraping
python src/pipeline.py --max-emails 100 --no-classify
```

## 📊 Exemplo de Resultado

```json
{
  "metadata": {
    "total_emails": 300,
    "classification_stats": {
      "total_images": 308,
      "classified_images": 308,
      "api_calls": 0
    }
  },
  "emails": [
    {
      "from": "João Silva <joao@example.com>",
      "subject": "Documentos cadastro",
      "attachments": [
        {
          "filename": "foto_3x4.jpg",
          "mimeType": "image/jpeg",
          "tag": ["FOTO_3X4"]
        },
        {
          "filename": "rg_frente.jpg", 
          "mimeType": "image/jpeg",
          "tag": ["RG"]
        }
      ]
    }
  ]
}
```

## 📈 Relatório de Performance

### Resultados da Classificação (Modo Teste)
- **Total de imagens**: 308
- **Emails com imagens**: 122 de 300
- **Eficácia**: 32.8% classificação automática

### Distribuição por Tipo
- 📸 **42 Fotos 3x4** (13.6%)
- 🏥 **24 Cartões SUS** (7.8%)  
- 🆔 **16 RGs** (5.2%)
- 👨‍⚕️ **11 CRMs** (3.6%)
- 📄 **8 CPFs** (2.6%)
- ⚠️ **207 Revisão Manual** (67.2%)

## 🔧 Personalização

### Adicionar Novo Tipo de Documento
1. Adicione em `DocumentClassifier.TAG_TYPES`
2. Implemente lógica em `classify_by_ocr_keywords()`
3. Adicione dados de teste em `analyze_image()`

### Empresas Locais (Comprovantes)
Edite `DocumentClassifier.LOCAL_UTILITIES`:
```python
LOCAL_UTILITIES = [
    "empresa luz e força santa maria",
    "edp es distrib de energia", 
    "enel",
    # Adicione mais empresas...
]
```

## 💰 Custos

### Modo Teste
- **Gratuito** - Classificação baseada em nomes de arquivo

### Google Cloud Vision API  
- **$1.50 por 1000 imagens**
- Para 308 imagens: ~$0.46
- Primeira 1000 imagens/mês: gratuitas

## 🚨 Troubleshooting

### Erro: "OAuth detectado, Vision API requer Service Account"
**Solução**: Use `--test-mode` ou configure service account

### Muitos documentos como "REVISAO_MANUAL"
**Soluções**:
- Use API real em vez de modo teste
- Melhore qualidade das imagens
- Ajuste heurísticas de classificação

### Arquivo não encontrado
**Solução**: Verifique se `emails_data.json` existe e caminhos dos anexos

## 📚 Documentação Detalhada

- [DOCUMENT_CLASSIFICATION.md](DOCUMENT_CLASSIFICATION.md) - Detalhes da classificação
- [OAUTH_ENV_SETUP.md](OAUTH_ENV_SETUP.md) - Configuração OAuth

## 🤝 Contribuição

1. Fork o projeto
2. Crie branch: `git checkout -b feature/nova-funcionalidade`
3. Commit: `git commit -m 'Adiciona nova funcionalidade'`
4. Push: `git push origin feature/nova-funcionalidade`
5. Abra Pull Request

## 📄 Licença

Este projeto está sob licença MIT. Veja `LICENSE` para detalhes.

## ✨ Recursos Avançados

- **Cache de OCR** para evitar reprocessamento
- **Detecção de rostos** para fotos 3x4
- **Regex inteligente** para padrões brasileiros
- **Relatórios visuais** com emojis e estatísticas
- **Modo batch** para grandes volumes
- **Fallback robusto** para casos não identificados

---

**Desenvolvido para otimizar o processamento de documentos médicos com IA** 🚀
