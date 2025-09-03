"""
Script para classificação automática de documentos médicos usando Google Cloud Vision API
"""

import json
import os
import re
import base64
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import time

try:
    from google.cloud import vision
    from google.oauth2.service_account import Credentials
except ImportError:
    print("❌ Google Cloud Vision não instalado. Execute: pip install google-cloud-vision")
    exit(1)


class DocumentClassifier:
    """Classificador de documentos médicos usando Google Cloud Vision API"""
    
    TAG_TYPES = [
        "RG",
        "CPF", 
        "CNH",
        "FOTO_3X4",
        "COMPROVANTE_ENDERECO",
        "CARTAO_SUS",
        "CRM",
        "TITULO_ELEITOR",
        "DIPLOMA_MEDICINA",
        "CERTIDAO_CASAMENTO",
        "PIS",
        "CARTEIRA_TRABALHO",
        "CERTIFICADO_ACLS",
        "CERTIFICADO_ATLS", 
        "CERTIFICADO_PALS",
        "CERTIFICADO_CURSO_OUTROS",
        "CERTIFICADO_ESPECIALIDADE",
        "CERTIFICADO_POS_GRADUACAO",
        "DECLARACAO_RESIDENCIA_MEDICA",
        "CURRICULO"
    ]
    
    # Empresas locais para comprovantes de endereço
    LOCAL_UTILITIES = [
        "empresa luz e força santa maria",
        "edp es distrib de energia",
        "enel",
        "loga administracao",
        "ultragaz", 
        "wk imoveis",
        "unimed vitória"
    ]
    
    # Regex para detectar foto 3x4 pelo nome do arquivo
    FOTO_3X4_REGEX = re.compile(r"(?i)^(?:foto[- ]?3x4|foto|3x4)\.(png|jpeg|jpg)$")
    
    def __init__(self, credentials_path: str = "credentials.json", test_mode: bool = False):
        """
        Inicializa o classificador
        
        Args:
            credentials_path: Caminho para o arquivo de credenciais do Google Cloud
            test_mode: Se True, executa em modo de teste sem chamar a API
        """
        self.credentials_path = credentials_path
        self.client = None
        self.processed_count = 0
        self.api_calls_count = 0
        self.test_mode = test_mode
        
        # Cache para OCR já processado
        self.ocr_cache = {}
        
    def authenticate(self) -> bool:
        """
        Autentica com Google Cloud Vision API
        
        Returns:
            bool: True se autenticação foi bem-sucedida
        """
        if self.test_mode:
            print("✅ Modo de teste ativado - pulando autenticação")
            return True
            
        try:
            if not os.path.exists(self.credentials_path):
                print(f"❌ Arquivo de credenciais não encontrado: {self.credentials_path}")
                print("💡 Para usar a Google Cloud Vision API, você precisa:")
                print("   1. Criar um projeto no Google Cloud Console")
                print("   2. Ativar a Vision API")
                print("   3. Criar uma service account e baixar o arquivo JSON")
                print("   4. Salvar como 'google_cloud_credentials.json'")
                print("   5. Ou usar --test-mode para execução sem API")
                return False
                
            # Verifica se é arquivo de service account (não OAuth)
            with open(self.credentials_path, 'r') as f:
                creds_data = json.load(f)
                if "installed" in creds_data:
                    print("❌ Arquivo de credenciais OAuth detectado. Vision API requer Service Account.")
                    print("💡 Use google_cloud_credentials.json ou --test-mode")
                    return False
                
            # Configura as credenciais
            credentials = Credentials.from_service_account_file(self.credentials_path)
            self.client = vision.ImageAnnotatorClient(credentials=credentials)
            
            print("✅ Autenticação com Google Cloud Vision realizada com sucesso")
            return True
            
        except Exception as e:
            print(f"❌ Erro na autenticação: {str(e)}")
            print("💡 Use --test-mode para execução sem API")
            return False
    
    def is_foto_3x4_by_filename(self, filename: str) -> bool:
        """
        Verifica se é foto 3x4 pelo nome do arquivo
        
        Args:
            filename: Nome do arquivo
            
        Returns:
            bool: True se parece ser foto 3x4
        """
        return bool(self.FOTO_3X4_REGEX.match(filename))
    
    def detect_foto_3x4_by_content(self, label_annotations: List, face_annotations: List, text_annotations: List) -> bool:
        """
        Detecta foto 3x4 baseado no conteúdo da imagem
        
        Args:
            label_annotations: Anotações de labels da Vision API
            face_annotations: Anotações de rostos
            text_annotations: Anotações de texto
            
        Returns:
            bool: True se parece ser foto 3x4
        """
        # Verifica se tem pelo menos um rosto detectado
        has_face = len(face_annotations) > 0
        
        # Verifica se tem pouco texto (foto 3x4 geralmente não tem texto)
        if self.test_mode:
            text_content = " ".join(text_annotations) if text_annotations else ""
        else:
            text_content = " ".join([text.description for text in text_annotations[:5]])  # Primeiros 5 textos
        has_little_text = len(text_content.strip()) < 50
        
        # Verifica labels que indicam pessoa/foto
        if self.test_mode:
            person_labels = ["person", "face", "head", "portrait", "human", "people"]
            has_person_labels = any(keyword in str(label_annotations).lower() for keyword in person_labels)
        else:
            person_labels = ["person", "face", "head", "portrait", "human", "people"]
            has_person_labels = any(
                any(keyword in label.description.lower() for keyword in person_labels)
                for label in label_annotations[:10]  # Top 10 labels
            )
        
        return has_face and has_little_text and has_person_labels
    
    def classify_by_ocr_keywords(self, text_content: str) -> Optional[str]:
        """
        Classifica documento baseado em palavras-chave do OCR
        
        Args:
            text_content: Texto extraído da imagem
            
        Returns:
            str: Tag do documento ou None se não identificado
        """
        text_lower = text_content.lower()
        
        # RG - Registro Geral
        rg_keywords = ["registro geral", "carteira de identidade", "identidade", "rg nº", "rg:", "doc. identidade"]
        if any(keyword in text_lower for keyword in rg_keywords):
            return "RG"
            
        # CPF
        cpf_keywords = ["cadastro de pessoa física", "cpf", "receita federal"]
        cpf_pattern = r"\d{3}\.\d{3}\.\d{3}-\d{2}"
        if any(keyword in text_lower for keyword in cpf_keywords) or re.search(cpf_pattern, text_content):
            return "CPF"
            
        # CNH
        cnh_keywords = ["carteira nacional de habilitação", "cnh", "detran", "habilitação"]
        if any(keyword in text_lower for keyword in cnh_keywords):
            return "CNH"
            
        # Cartão SUS
        sus_keywords = ["sistema único de saúde", "sus", "cartão nacional de saúde", "cns"]
        if any(keyword in text_lower for keyword in sus_keywords):
            return "CARTAO_SUS"
            
        # CRM
        crm_keywords = ["conselho regional de medicina", "crm", "medicina"]
        if any(keyword in text_lower for keyword in crm_keywords):
            return "CRM"
            
        # Título de Eleitor
        titulo_keywords = ["título de eleitor", "titulo eleitor", "justiça eleitoral", "tse"]
        if any(keyword in text_lower for keyword in titulo_keywords):
            return "TITULO_ELEITOR"
            
        # Diploma de Medicina
        diploma_keywords = ["diploma", "bacharel", "medicina", "universidade", "graduação"]
        if "diploma" in text_lower and "medicina" in text_lower:
            return "DIPLOMA_MEDICINA"
            
        # Certidão de Casamento
        casamento_keywords = ["certidão de casamento", "cartório", "casamento"]
        if any(keyword in text_lower for keyword in casamento_keywords):
            return "CERTIDAO_CASAMENTO"
            
        # PIS
        pis_keywords = ["pis", "pasep", "programa de integração social"]
        if any(keyword in text_lower for keyword in pis_keywords):
            return "PIS"
            
        # Carteira de Trabalho
        trabalho_keywords = ["carteira de trabalho", "ctps", "ministério do trabalho"]
        if any(keyword in text_lower for keyword in trabalho_keywords):
            return "CARTEIRA_TRABALHO"
            
        # Certificados
        if "certificado" in text_lower or "certificação" in text_lower:
            if "acls" in text_lower:
                return "CERTIFICADO_ACLS"
            elif "atls" in text_lower:
                return "CERTIFICADO_ATLS"
            elif "pals" in text_lower:
                return "CERTIFICADO_PALS"
            elif any(keyword in text_lower for keyword in ["especialidade", "especialização"]):
                return "CERTIFICADO_ESPECIALIDADE"
            elif any(keyword in text_lower for keyword in ["pós-graduação", "pos graduacao", "especialização"]):
                return "CERTIFICADO_POS_GRADUACAO"
            else:
                return "CERTIFICADO_CURSO_OUTROS"
                
        # Declaração de Residência Médica
        residencia_keywords = ["residência médica", "residencia medica", "programa de residência"]
        if any(keyword in text_lower for keyword in residencia_keywords):
            return "DECLARACAO_RESIDENCIA_MEDICA"
            
        # Currículo
        curriculo_keywords = ["currículo", "curriculum", "cv", "experiência profissional"]
        if any(keyword in text_lower for keyword in curriculo_keywords):
            return "CURRICULO"
            
        # Comprovante de Endereço
        endereco_keywords = ["comprovante", "endereço", "residência"]
        utility_found = any(utility in text_lower for utility in self.LOCAL_UTILITIES)
        
        if utility_found or any(keyword in text_lower for keyword in endereco_keywords):
            return "COMPROVANTE_ENDERECO"
            
        return None
    
    def analyze_image(self, image_path: str) -> Tuple[List, List, List]:
        """
        Analisa imagem com Google Cloud Vision API
        
        Args:
            image_path: Caminho para a imagem
            
        Returns:
            Tuple: (label_annotations, face_annotations, text_annotations)
        """
        if self.test_mode:
            # Modo de teste: retorna dados simulados baseados no nome do arquivo
            filename = os.path.basename(image_path).lower()
            print(f"   🧪 Modo teste - simulando análise de: {filename}")
            
            # Simula detecções baseadas no nome do arquivo
            mock_labels = []
            mock_faces = []
            mock_text = []
            
            if "foto" in filename or "3x4" in filename:
                mock_faces = ["mock_face"]  # Simula detecção de rosto
                mock_text = ["Nome da Pessoa"]  # Pouco texto
            elif "rg" in filename or "identidade" in filename:
                mock_text = ["REPÚBLICA FEDERATIVA DO BRASIL", "REGISTRO GERAL", "123456789"]
            elif "cpf" in filename:
                mock_text = ["RECEITA FEDERAL", "CPF", "123.456.789-00"]
            elif "crm" in filename:
                mock_text = ["CONSELHO REGIONAL DE MEDICINA", "CRM-ES", "12345"]
            elif "sus" in filename or "cns" in filename:
                mock_text = ["SISTEMA ÚNICO DE SAÚDE", "CNS", "7000000000000"]
                
            return mock_labels, mock_faces, mock_text
            
        try:
            with open(image_path, 'rb') as image_file:
                content = image_file.read()
            
            image = vision.Image(content=content)
            
            # Primeira chamada: LABEL_DETECTION + TEXT_DETECTION
            features = [
                vision.Feature(type_=vision.Feature.Type.LABEL_DETECTION, max_results=10),
                vision.Feature(type_=vision.Feature.Type.TEXT_DETECTION, max_results=1)
            ]
            
            request = vision.AnnotateImageRequest(image=image, features=features)
            response = self.client.annotate_image(request=request)
            
            if response.error.message:
                raise Exception(f'{response.error.message}')
                
            self.api_calls_count += 1
            
            label_annotations = response.label_annotations
            text_annotations = response.text_annotations
            face_annotations = []
            
            # Se OCR está quase vazio, faça segunda chamada para FACE_DETECTION
            text_content = text_annotations[0].description if text_annotations else ""
            if len(text_content.strip()) < 10:  # Pouco texto detectado
                face_features = [vision.Feature(type_=vision.Feature.Type.FACE_DETECTION, max_results=5)]
                face_request = vision.AnnotateImageRequest(image=image, features=face_features)
                face_response = self.client.annotate_image(request=face_request)
                
                if not face_response.error.message:
                    face_annotations = face_response.face_annotations
                    self.api_calls_count += 1
            
            return label_annotations, face_annotations, text_annotations
            
        except Exception as e:
            print(f"⚠️  Erro ao analisar imagem {image_path}: {str(e)}")
            return [], [], []
    
    def classify_attachment(self, attachment: Dict[str, Any], base_path: str = "") -> Optional[str]:
        """
        Classifica um anexo específico
        
        Args:
            attachment: Dicionário do anexo
            base_path: Caminho base para os arquivos
            
        Returns:
            str: Tag classificada ou None
        """
        filename = attachment.get("filename", "")
        anexo_path = attachment.get("anexoPath", "")
        
        # Primeiro verifica se é foto 3x4 pelo nome
        if self.is_foto_3x4_by_filename(filename):
            return "FOTO_3X4"
        
        # Constrói caminho completo para o arquivo
        full_path = os.path.join(base_path, anexo_path) if base_path else anexo_path
        
        if not os.path.exists(full_path):
            print(f"⚠️  Arquivo não encontrado: {full_path}")
            return "REVISAO_MANUAL"
        
        # Analisa com Vision API
        label_annotations, face_annotations, text_annotations = self.analyze_image(full_path)
        
        # Extrai texto para análise
        if self.test_mode:
            text_content = " ".join(text_annotations) if text_annotations else ""
        else:
            text_content = text_annotations[0].description if text_annotations else ""
        
        # Cache do OCR
        self.ocr_cache[full_path] = text_content
        
        # Verifica se é foto 3x4 pelo conteúdo
        if self.detect_foto_3x4_by_content(label_annotations, face_annotations, text_annotations):
            return "FOTO_3X4"
        
        # Classifica por palavras-chave do OCR
        classified_tag = self.classify_by_ocr_keywords(text_content)
        if classified_tag:
            return classified_tag
            
        # Fallback: revisão manual
        return "REVISAO_MANUAL"
    
    def process_emails_data(self, input_file: str, output_file: str = "emails.json", base_path: str = "") -> bool:
        """
        Processa o arquivo de dados de emails e classifica anexos de imagem
        
        Args:
            input_file: Arquivo JSON de entrada
            output_file: Arquivo JSON de saída
            base_path: Caminho base para os arquivos de anexo
            
        Returns:
            bool: True se processamento foi bem-sucedido
        """
        print(f"📊 Iniciando classificação de documentos...")
        print(f"   Entrada: {input_file}")
        print(f"   Saída: {output_file}")
        
        # Autentica com Google Cloud Vision
        if not self.authenticate():
            return False
        
        try:
            # Carrega dados
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            image_count = 0
            processed_image_count = 0
            
            # Processa cada email
            for email in data.get("emails", []):
                attachments = email.get("attachments", [])
                
                for attachment in attachments:
                    mime_type = attachment.get("mimeType", "")
                    
                    # Processa apenas imagens
                    if mime_type.startswith("image/"):
                        image_count += 1
                        print(f"🔍 Classificando imagem {image_count}: {attachment.get('filename', 'sem nome')}")
                        
                        # Classifica anexo
                        tag = self.classify_attachment(attachment, base_path)
                        
                        if tag:
                            attachment["tag"] = [tag]
                            processed_image_count += 1
                            print(f"   ✅ Classificado como: {tag}")
                        else:
                            attachment["tag"] = ["REVISAO_MANUAL"]
                            print(f"   ⚠️  Necessita revisão manual")
                        
                        # Pequena pausa para não sobrecarregar a API
                        time.sleep(0.1)
            
            # Atualiza metadados
            if "metadata" not in data:
                data["metadata"] = {}
            
            data["metadata"]["classification_stats"] = {
                "total_images": image_count,
                "classified_images": processed_image_count,
                "api_calls": self.api_calls_count,
                "processed_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Salva resultado
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print("\n" + "="*60)
            print("📊 RESUMO DA CLASSIFICAÇÃO")
            print("="*60)
            print(f"Total de imagens: {image_count}")
            print(f"Imagens classificadas: {processed_image_count}")
            print(f"Chamadas à API: {self.api_calls_count}")
            print(f"Arquivo de saída: {output_file}")
            print("="*60)
            
            return True
            
        except Exception as e:
            print(f"❌ Erro durante o processamento: {str(e)}")
            return False


def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Classificador de documentos médicos')
    parser.add_argument('--input', default='emails_data.json', help='Arquivo JSON de entrada')
    parser.add_argument('--output', default='emails.json', help='Arquivo JSON de saída')
    parser.add_argument('--base-path', default='', help='Caminho base para arquivos de anexo')
    parser.add_argument('--credentials', default='google_cloud_credentials.json', help='Arquivo de credenciais Google Cloud')
    parser.add_argument('--test-mode', action='store_true', help='Executa em modo de teste sem chamar a API')
    
    args = parser.parse_args()
    
    classifier = DocumentClassifier(
        credentials_path=args.credentials,
        test_mode=args.test_mode
    )
    success = classifier.process_emails_data(
        input_file=args.input,
        output_file=args.output,
        base_path=args.base_path
    )
    
    if success:
        print("✅ Classificação concluída com sucesso!")
    else:
        print("❌ Falha na classificação!")
    
    return success


if __name__ == "__main__":
    main()
