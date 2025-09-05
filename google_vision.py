import json
import os
from google.cloud import vision
from typing import List, Dict, Any

# Cliente do Google Vision
client = vision.ImageAnnotatorClient()

# Tipos de documentos possíveis
TAG_TYPES = [
    "RG", "CPF", "CNH", "FOTO_3X4", "COMPROVANTE_ENDERECO", 
    "CARTAO_SUS", "CRM", "TITULO_ELEITOR", "DIPLOMA_MEDICINA",
    "CERTIDAO_CASAMENTO", "PIS", "CARTEIRA_TRABALHO",
    "CERTIFICADO_ACLS", "CERTIFICADO_ATLS", "CERTIFICADO_PALS",
    "CERTIFICADO_CURSO_OUTROS", "CERTIFICADO_ESPECIALIDADE",
    "CERTIFICADO_POS_GRADUACAO", "DECLARACAO_RESIDENCIA_MEDICA", "CURRICULO"
]

# Dicionário de empresas de utilidades para comprovantes
UTILITY_COMPANIES = [
    "empresa luz e força santa maria", "edp es distrib de energia",
    "enel", "loga administracao", "ultragaz", "wk imoveis", "unimed vitória"
]

def analyze_image_with_vision(image_path: str) -> Dict[str, Any]:
    """Analisa uma imagem usando múltiplas features do Google Vision API"""
    try:
        with open(image_path, "rb") as image_file:
            content = image_file.read()
        
        image = vision.Image(content=content)
        
        # Configurar múltiplas features numa única chamada
        features = [
            vision.Feature(type=vision.Feature.Type.TEXT_DETECTION),
            vision.Feature(type=vision.Feature.Type.LABEL_DETECTION),
        ]
        
        # Criar requisição com múltiplas features
        request = vision.AnnotateImageRequest(
            image=image,
            features=features
        )
        
        # Fazer chamada única à API
        response = client.annotate_image(request=request)
        
        return {
            'text': response.full_text_annotation.text if response.full_text_annotation.text else "",
            'labels': [label.description.lower() for label in response.label_annotations],
            'error': None
        }
    except Exception as e:
        print(f"Erro ao processar {image_path}: {str(e)}")
        return {'text': "", 'labels': [], 'error': str(e)}

def identify_document_type(vision_result: Dict[str, Any], filename: str) -> str:
    """Identifica o tipo de documento baseado nos resultados do Vision API"""
    
    text = vision_result['text'].lower() if vision_result['text'] else ""
    labels = vision_result['labels']
    filename_lower = filename.lower()
    
    # 2. RG - Registro Geral
    if any(term in text for term in ['registro geral', 'rg:', 'identidade', 'ssp', 'secretaria de segurança']):
        return "RG"
    
    # 3. CPF
    if any(term in text for term in ['cadastro de pessoas físicas', 'cpf:', 'receita federal']):
        return "CPF"
    
    # 4. CNH - Carteira Nacional de Habilitação
    if any(term in text for term in ['carteira nacional de habilitação', 'cnh', 'detran', 'habilitação']):
        return "CNH"
    
    # 5. COMPROVANTE_ENDERECO
    if any(company in text for company in UTILITY_COMPANIES):
        return "COMPROVANTE_ENDERECO"
    if any(term in text for term in ['conta de luz', 'conta de água', 'conta de gás', 'fatura', 'vencimento']):
        return "COMPROVANTE_ENDERECO"
    
    # 6. CARTAO_SUS
    if any(term in text for term in ['cartão nacional de saúde', 'sus', 'cns', 'ministério da saúde']):
        return "CARTAO_SUS"
    
    # 7. CRM
    if any(term in text for term in ['conselho regional de medicina', 'crm', 'registro médico']):
        return "CRM"
    
    # 8. TITULO_ELEITOR
    if any(term in text for term in ['título de eleitor', 'justiça eleitoral', 'zona eleitoral']):
        return "TITULO_ELEITOR"
    
    # 9. DIPLOMA_MEDICINA
    if any(term in text for term in ['diploma', 'bacharel', 'medicina', 'universidade']) and 'medicina' in text:
        return "DIPLOMA_MEDICINA"
    
    # 10. CERTIDAO_CASAMENTO
    if any(term in text for term in ['certidão de casamento', 'matrimônio', 'cônjuge']):
        return "CERTIDAO_CASAMENTO"
    
    # 11. PIS
    if any(term in text for term in ['pis', 'pasep', 'programa de integração social']):
        return "PIS"
    
    # 12. CARTEIRA_TRABALHO
    if any(term in text for term in ['carteira de trabalho', 'ctps', 'ministério do trabalho']):
        return "CARTEIRA_TRABALHO"
    
    # 13. Certificados ACLS/ATLS/PALS
    if 'acls' in text or 'advanced cardiac life support' in text:
        return "CERTIFICADO_ACLS"
    if 'atls' in text or 'advanced trauma life support' in text:
        return "CERTIFICADO_ATLS"
    if 'pals' in text or 'pediatric advanced life support' in text:
        return "CERTIFICADO_PALS"
    
    # 14. CERTIFICADO_ESPECIALIDADE
    if any(term in text for term in ['especialização', 'especialista', 'residência médica']):
        return "CERTIFICADO_ESPECIALIDADE"
    
    # 15. CERTIFICADO_POS_GRADUACAO
    if any(term in text for term in ['pós-graduação', 'pós graduação', 'mestrado', 'doutorado']):
        return "CERTIFICADO_POS_GRADUACAO"
    
    # 16. DECLARACAO_RESIDENCIA_MEDICA
    if 'residência médica' in text and 'declaração' in text:
        return "DECLARACAO_RESIDENCIA_MEDICA"
    
    # 17. CURRICULO
    if any(term in text for term in ['currículo', 'curriculum', 'formação acadêmica', 'experiência profissional']):
        return "CURRICULO"
    
    # 18. CERTIFICADO_CURSO_OUTROS (genérico para outros certificados)
    if any(term in text for term in ['certificado', 'curso', 'participação', 'conclusão']):
        return "CERTIFICADO_CURSO_OUTROS"
    
    # Fallback
    return "NONE"

def process_emails_json(json_path: str):
    """Processa o arquivo emails.json e adiciona tag_ai para imagens com AI_VISION_IMAGE"""
    
    # Carregar o JSON
    with open(json_path, 'r', encoding='utf-8') as f:
        emails_data = json.load(f)
    
    processed_count = 0
    
    # Processar cada email
    for email in emails_data['emails']:
        # Processar cada anexo
        for attachment in email.get('attachments', []):
            # Verificar se tem a tag AI_VISION_IMAGE
            if 'AI_VISION_IMAGE' in attachment.get('tag', []):
                anexo_path = attachment.get('anexoPath', '')
                
                if anexo_path and os.path.exists(anexo_path):
                    print(f"\nProcessando: {anexo_path}")
                    
                    # Analisar imagem com Vision API
                    vision_result = analyze_image_with_vision(anexo_path)
                    
                    if not vision_result['error']:
                        # Identificar tipo de documento
                        doc_type = identify_document_type(vision_result, attachment.get('filename', ''))
                        
                        # Adicionar tag_ai
                        attachment['tag_ai'] = doc_type
                        processed_count += 1
                        
                        print(f"Tipo identificado: {doc_type}")
                        if vision_result['text']:
                            print(f"Texto detectado (primeiros 100 chars): {vision_result['text'][:100]}...")
                    else:
                        # Em caso de erro, marcar como NONE
                        attachment['tag_ai'] = "NONE"
                        print(f"Erro no processamento, marcado como NONE")
                else:
                    print(f"\nArquivo não encontrado: {anexo_path}")
                    attachment['tag_ai'] = "NONE"
    
    # Salvar o JSON atualizado
    output_path = 'emails_processed.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(emails_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n\nProcessamento concluído!")
    print(f"Total de imagens processadas: {processed_count}")
    print(f"Arquivo salvo em: {output_path}")

# Executar o processamento
if __name__ == "__main__":
    # Certifique-se de que as credenciais do Google Cloud estão configuradas
    # export GOOGLE_APPLICATION_CREDENTIALS="path/to/your/credentials.json"
    
    process_emails_json('images_v3.json')