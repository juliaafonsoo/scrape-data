"""
Script para processar apenas arquivos marcados como REVISAO_MANUAL usando Google Cloud Vision API
"""

import json
import os
import time
from typing import List, Dict, Any, Optional
from src.document_classifier import DocumentClassifier


class ManualReviewProcessor:
    """Processador específico para arquivos que precisam de revisão manual"""
    
    def __init__(self, credentials_path: str = "credentials.json", test_mode: bool = False):
        """
        Inicializa o processador
        
        Args:
            credentials_path: Caminho para o arquivo de credenciais do Google Cloud
            test_mode: Se True, executa em modo de teste sem chamar a API
        """
        self.classifier = DocumentClassifier(credentials_path, test_mode)
        self.processed_count = 0
        self.reclassified_count = 0
        
    def find_manual_review_files(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Encontra todos os arquivos marcados como REVISAO_MANUAL
        
        Args:
            data: Dados do arquivo JSON
            
        Returns:
            List: Lista de attachments que precisam de revisão manual
        """
        manual_files = []
        
        for email in data.get("emails", []):
            for attachment in email.get("attachments", []):
                # Verifica se tem tag REVISAO_MANUAL
                tags = attachment.get("tag", [])
                if "REVISAO_MANUAL" in tags:
                    # Adiciona informações do email para contexto
                    attachment_copy = attachment.copy()
                    attachment_copy["email_from"] = email.get("from", "")
                    attachment_copy["email_subject"] = email.get("subject", "")
                    attachment_copy["email_id"] = email.get("emailID", 0)
                    manual_files.append(attachment_copy)
        
        return manual_files
        
    def process_manual_review_files(self, input_file: str, output_file: str = None, base_path: str = "") -> bool:
        """
        Processa apenas os arquivos marcados como REVISAO_MANUAL
        
        Args:
            input_file: Arquivo JSON de entrada
            output_file: Arquivo JSON de saída (se None, sobrescreve o input)
            base_path: Caminho base para os arquivos de anexo
            
        Returns:
            bool: True se processamento foi bem-sucedido
        """
        if output_file is None:
            output_file = input_file
            
        print(f"🔍 Processando arquivos marcados como REVISAO_MANUAL...")
        print(f"   Entrada: {input_file}")
        print(f"   Saída: {output_file}")
        
        # Autentica com Google Cloud Vision
        if not self.classifier.authenticate():
            return False
        
        try:
            # Carrega dados
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Encontra arquivos para revisão manual
            manual_files = self.find_manual_review_files(data)
            total_manual_files = len(manual_files)
            
            if total_manual_files == 0:
                print("✅ Nenhum arquivo marcado como REVISAO_MANUAL encontrado!")
                return True
                
            print(f"📊 Encontrados {total_manual_files} arquivos para processamento")
            
            # Processa apenas arquivos de imagem
            image_files = [f for f in manual_files if f.get("mimeType", "").startswith("image/")]
            
            if len(image_files) == 0:
                print("ℹ️  Nenhum arquivo de imagem encontrado para processamento")
                return True
                
            print(f"🖼️  Processando {len(image_files)} imagens marcadas como REVISAO_MANUAL...")
            print("-" * 60)
            
            # Processa cada arquivo de imagem
            for i, file_info in enumerate(image_files, 1):
                filename = file_info.get("filename", "sem nome")
                anexo_path = file_info.get("anexoPath", "")
                email_from = file_info.get("email_from", "")
                attachment_id = file_info.get("attachmentID", 0)
                
                print(f"\n[{i}/{len(image_files)}] 🔍 Processando: {filename}")
                print(f"   📧 De: {email_from}")
                print(f"   📁 Caminho: {anexo_path}")
                
                # Reclassifica o arquivo
                new_tag = self.classifier.classify_attachment(file_info, base_path)
                
                if new_tag and new_tag != "REVISAO_MANUAL":
                    # Encontra e atualiza o attachment original nos dados
                    self._update_attachment_tag(data, attachment_id, new_tag)
                    self.reclassified_count += 1
                    print(f"   ✅ Reclassificado como: {new_tag}")
                else:
                    print(f"   ⚠️  Mantido como: REVISAO_MANUAL")
                
                self.processed_count += 1
                
                # Pequena pausa para não sobrecarregar a API
                time.sleep(0.2)
            
            # Atualiza metadados
            if "metadata" not in data:
                data["metadata"] = {}
            
            if "manual_review_processing" not in data["metadata"]:
                data["metadata"]["manual_review_processing"] = {}
                
            data["metadata"]["manual_review_processing"] = {
                "total_manual_files": total_manual_files,
                "image_files_processed": len(image_files),
                "reclassified_files": self.reclassified_count,
                "api_calls": self.classifier.api_calls_count,
                "processed_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Salva resultado
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print("\n" + "="*60)
            print("📊 RESUMO DO PROCESSAMENTO DE REVISÃO MANUAL")
            print("="*60)
            print(f"Total de arquivos REVISAO_MANUAL: {total_manual_files}")
            print(f"Imagens processadas: {len(image_files)}")
            print(f"Arquivos reclassificados: {self.reclassified_count}")
            print(f"Arquivos que permanecem REVISAO_MANUAL: {len(image_files) - self.reclassified_count}")
            print(f"Chamadas à API: {self.classifier.api_calls_count}")
            print(f"Arquivo de saída: {output_file}")
            print("="*60)
            
            return True
            
        except Exception as e:
            print(f"❌ Erro durante o processamento: {str(e)}")
            return False
    
    def _update_attachment_tag(self, data: Dict[str, Any], attachment_id: int, new_tag: str):
        """
        Atualiza a tag de um attachment específico nos dados
        
        Args:
            data: Dados completos do JSON
            attachment_id: ID do attachment para atualizar
            new_tag: Nova tag para aplicar
        """
        for email in data.get("emails", []):
            for attachment in email.get("attachments", []):
                if attachment.get("attachmentID") == attachment_id:
                    # Remove REVISAO_MANUAL e adiciona nova tag
                    current_tags = attachment.get("tag", [])
                    if "REVISAO_MANUAL" in current_tags:
                        current_tags.remove("REVISAO_MANUAL")
                    if new_tag not in current_tags:
                        current_tags.append(new_tag)
                    attachment["tag"] = current_tags
                    return
    
    def list_manual_review_files(self, input_file: str) -> bool:
        """
        Lista todos os arquivos marcados como REVISAO_MANUAL
        
        Args:
            input_file: Arquivo JSON de entrada
            
        Returns:
            bool: True se listagem foi bem-sucedida
        """
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            manual_files = self.find_manual_review_files(data)
            
            if len(manual_files) == 0:
                print("✅ Nenhum arquivo marcado como REVISAO_MANUAL encontrado!")
                return True
            
            print(f"\n📋 ARQUIVOS MARCADOS COMO REVISAO_MANUAL ({len(manual_files)} arquivos)")
            print("="*80)
            
            # Agrupa por tipo de arquivo
            image_files = []
            other_files = []
            
            for file_info in manual_files:
                mime_type = file_info.get("mimeType", "")
                if mime_type.startswith("image/"):
                    image_files.append(file_info)
                else:
                    other_files.append(file_info)
            
            # Lista arquivos de imagem (que podem ser processados)
            if image_files:
                print(f"\n🖼️  IMAGENS ({len(image_files)} arquivos - PODEM SER PROCESSADOS):")
                print("-" * 60)
                for i, file_info in enumerate(image_files, 1):
                    filename = file_info.get("filename", "sem nome")
                    email_from = file_info.get("email_from", "").split("<")[0].strip()
                    anexo_path = file_info.get("anexoPath", "")
                    print(f"{i:3d}. {filename}")
                    print(f"     📧 De: {email_from}")
                    print(f"     📁 {anexo_path}")
                    print()
            
            # Lista outros tipos de arquivo
            if other_files:
                print(f"\n📄 OUTROS ARQUIVOS ({len(other_files)} arquivos - NÃO PROCESSÁVEIS COM VISION API):")
                print("-" * 60)
                for i, file_info in enumerate(other_files, 1):
                    filename = file_info.get("filename", "sem nome")
                    mime_type = file_info.get("mimeType", "")
                    email_from = file_info.get("email_from", "").split("<")[0].strip()
                    print(f"{i:3d}. {filename} ({mime_type})")
                    print(f"     📧 De: {email_from}")
                    print()
            
            print("="*80)
            print(f"📊 RESUMO:")
            print(f"   • Total: {len(manual_files)} arquivos")
            print(f"   • Imagens (processáveis): {len(image_files)}")
            print(f"   • Outros tipos: {len(other_files)}")
            print("="*80)
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao listar arquivos: {str(e)}")
            return False


def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Processador de arquivos marcados como REVISAO_MANUAL')
    parser.add_argument('--input', default='emails.json', help='Arquivo JSON de entrada')
    parser.add_argument('--output', help='Arquivo JSON de saída (padrão: sobrescreve input)')
    parser.add_argument('--base-path', default='', help='Caminho base para arquivos de anexo')
    parser.add_argument('--credentials', default='credentials.json', help='Arquivo de credenciais Google Cloud')
    parser.add_argument('--test-mode', action='store_true', help='Executa em modo de teste sem chamar a API')
    parser.add_argument('--list-only', action='store_true', help='Apenas lista os arquivos REVISAO_MANUAL sem processar')
    
    args = parser.parse_args()
    
    processor = ManualReviewProcessor(
        credentials_path=args.credentials,
        test_mode=args.test_mode
    )
    
    if args.list_only:
        success = processor.list_manual_review_files(args.input)
    else:
        success = processor.process_manual_review_files(
            input_file=args.input,
            output_file=args.output,
            base_path=args.base_path
        )
    
    if success:
        if args.list_only:
            print("✅ Listagem concluída com sucesso!")
        else:
            print("✅ Processamento concluído com sucesso!")
    else:
        print("❌ Falha no processamento!")
    
    return success


if __name__ == "__main__":
    main()
