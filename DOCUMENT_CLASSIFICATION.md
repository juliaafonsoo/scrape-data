# Sistema de Classificação Automática de Documentos Médicos

Este sistema utiliza a Google Cloud Vision API para classificar automaticamente documentos médicos anexados em emails, identificando tipos como RG, CPF, CNH, fotos 3x4, comprovantes de endereço, entre outros.

## Funcionalidades

### Tags Suportadas

O sistema classifica documentos nas seguintes categorias:

- **RG** - Registro Geral/Carteira de Identidade
- **CPF** - Cadastro de Pessoa Física  
- **CNH** - Carteira Nacional de Habilitação
- **FOTO_3X4** - Fotos 3x4 para documentos
- **COMPROVANTE_ENDERECO** - Comprovantes de residência
- **CARTAO_SUS** - Cartão Nacional de Saúde/CNS
- **CRM** - Registro no Conselho Regional de Medicina
- **TITULO_ELEITOR** - Título de Eleitor
- **DIPLOMA_MEDICINA** - Diploma de graduação em Medicina
- **CERTIDAO_CASAMENTO** - Certidão de Casamento
- **PIS** - Documento PIS/PASEP
- **CARTEIRA_TRABALHO** - Carteira de Trabalho
- **CERTIFICADO_ACLS** - Certificação ACLS
- **CERTIFICADO_ATLS** - Certificação ATLS
- **CERTIFICADO_PALS** - Certificação PALS
- **CERTIFICADO_CURSO_OUTROS** - Outros certificados de cursos
- **CERTIFICADO_ESPECIALIDADE** - Certificados de especialidade médica
- **CERTIFICADO_POS_GRADUACAO** - Certificados de pós-graduação
- **DECLARACAO_RESIDENCIA_MEDICA** - Declarações de residência médica
- **CURRICULO** - Currículos
- **REVISAO_MANUAL** - Documentos que necessitam revisão manual

### Estratégias de Classificação

1. **Detecção por Nome de Arquivo**: Identifica fotos 3x4 pelo padrão regex `(?i)^(?:foto[- ]?3x4|foto|3x4)\.(png|jpeg|jpg)$`

2. **Análise por Conteúdo**: Utiliza Google Cloud Vision API para:
   - **LABEL_DETECTION**: Identifica objetos e conceitos na imagem
   - **TEXT_DETECTION**: Extrai texto via OCR
   - **FACE_DETECTION**: Detecta rostos (usado apenas quando há pouco texto)

3. **Classificação por Heurísticas**: Aplica regras baseadas em palavras-chave do OCR:
   - Busca termos específicos em cada tipo de documento
   - Considera empresas locais para comprovantes de endereço
   - Detecta padrões como CPF (###.###.###-##)

## Como Usar

### Pré-requisitos

1. **Python 3.7+** com ambiente virtual ativado
2. **Dependências instaladas**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Google Cloud Vision API** (opcional para modo real):
   - Criar projeto no Google Cloud Console
   - Ativar a Vision API
   - Criar service account e baixar credenciais JSON
   - Salvar como `google_cloud_credentials.json`

### Execução

#### Modo de Teste (Sem API)
```bash
python classify_documents.py --test-mode
```

#### Modo Real (Com Google Cloud Vision API)
```bash
python classify_documents.py --input emails_data.json --output emails_classified.json
```

#### Via Pipeline Integrado
```bash
# Com classificação automática
python src/pipeline.py --classify

# Sem classificação
python src/pipeline.py --no-classify
```

### Parâmetros

- `--input`: Arquivo JSON de entrada (padrão: `emails_data.json`)
- `--output`: Arquivo JSON de saída (padrão: `emails.json`)
- `--test-mode`: Executa sem chamar a API, usando dados simulados
- `--credentials`: Arquivo de credenciais do Google Cloud (padrão: `google_cloud_credentials.json`)

## Estrutura de Saída

O arquivo de saída mantém a estrutura original dos emails, adicionando tags aos anexos de imagem:

```json
{
  "metadata": {
    "total_emails": 300,
    "processed_at": "2025-08-30T21:08:13.219034",
    "label_used": "DOC-MEDICOS",
    "classification_stats": {
      "total_images": 308,
      "classified_images": 308,
      "api_calls": 0,
      "processed_at": "2025-08-31 23:30:17"
    }
  },
  "emails": [
    {
      "from": "João Silva <joao@example.com>",
      "subject": "Documentos para cadastro",
      "body": "Segue documentos...",
      "attachments": [
        {
          "filename": "foto_3x4.jpg",
          "mimeType": "image/jpeg",
          "anexoPath": "anexos-email/João Silva/foto_3x4.jpg",
          "attachmentID": 1,
          "tag": ["FOTO_3X4"]
        },
        {
          "filename": "rg_frente.jpg",
          "mimeType": "image/jpeg", 
          "anexoPath": "anexos-email/João Silva/rg_frente.jpg",
          "attachmentID": 2,
          "tag": ["RG"]
        }
      ],
      "emailID": 1
    }
  ]
}
```

## Empresas Locais Reconhecidas

Para comprovantes de endereço, o sistema reconhece as seguintes empresas locais:

- Empresa Luz e Força Santa Maria
- EDP ES Distrib de Energia  
- Enel
- LOGA Administração
- Ultragaz
- WK Imóveis
- Unimed Vitória

## Monitoramento e Logs

O sistema fornece logs detalhados durante a execução:

- ✅ Documentos classificados com sucesso
- ⚠️ Documentos que necessitam revisão manual
- 🧪 Indicação quando em modo de teste
- 📊 Relatório final com estatísticas

## Limitações

1. **Modo Teste**: Classificação baseada apenas em nomes de arquivos
2. **API Limits**: Google Cloud Vision API tem limites de uso
3. **Idioma**: Otimizado para documentos em português brasileiro
4. **Qualidade**: Depende da qualidade das imagens escaneadas

## Troubleshooting

### Erro de Autenticação
```
❌ Arquivo de credenciais OAuth detectado. Vision API requer Service Account.
```
**Solução**: Use credenciais de service account ou execute com `--test-mode`

### Arquivo Não Encontrado
```
⚠️ Arquivo não encontrado: /caminho/para/imagem.jpg
```
**Solução**: Verifique se os caminhos dos anexos estão corretos

### Muitos Documentos como "REVISAO_MANUAL"
**Solução**: 
- Verifique a qualidade das imagens
- Considere usar a API real em vez do modo de teste
- Ajuste as heurísticas de classificação se necessário

## Desenvolvimento

Para adicionar novos tipos de documentos:

1. Adicione o tipo em `DocumentClassifier.TAG_TYPES`
2. Implemente lógica de detecção em `classify_by_ocr_keywords()`
3. Adicione dados simulados em `analyze_image()` para modo de teste
4. Teste com documentos reais

## Custos

- **Modo Teste**: Gratuito
- **Google Cloud Vision API**: ~$1.50 por 1000 imagens
- Para 300+ imagens, custo estimado: < $0.50
