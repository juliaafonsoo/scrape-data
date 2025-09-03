"""
Pipeline de orquestração de ponta a ponta para scraping de emails
"""

import json
import sys
import os
from typing import List, Dict, Any
from datetime import datetime

# Adiciona o diretório src ao path para imports relativos
sys.path.insert(0, os.path.dirname(__file__))

from auth import validate_authentication, LABEL_NAME
from gmail_client import GmailClient
from models import EmailData
from utils import save_emails_to_json
from document_classifier import DocumentClassifier


class EmailScrapingPipeline:
    """Pipeline principal para scraping e processamento de emails"""
    
    def __init__(self):
        """Inicializa o pipeline"""
        self.gmail_client = None
        self.processed_emails = []
    
    def setup(self) -> bool:
        """
        Configura e valida as conexões necessárias
        
        Returns:
            bool: True se setup foi bem-sucedido
        """
        print("🔧 Configurando pipeline...")
        
        # Valida autenticação
        if not validate_authentication():
            print("❌ Falha na autenticação")
            return False
        
        # Inicializa cliente Gmail
        try:
            self.gmail_client = GmailClient()
            print("✅ Cliente Gmail inicializado")
            return True
        except Exception as e:
            print(f"❌ Erro ao inicializar cliente Gmail: {str(e)}")
            return False
    
    def run_full_pipeline(self, label_name: str = LABEL_NAME, max_emails: int = 100, output_file: str = None, classify_documents: bool = True) -> bool:
        """
        Executa o pipeline completo de scraping
        
        Args:
            label_name: Nome do label para filtrar emails
            max_emails: Número máximo de emails para processar
            output_file: Arquivo de saída (opcional)
            classify_documents: Se True, classifica documentos usando Vision API
            
        Returns:
            bool: True se pipeline executou com sucesso
        """
        print(f"🚀 Iniciando pipeline de scraping...")
        print(f"   Label: {label_name}")
        print(f"   Max emails: {max_emails}")
        print(f"   Classificar documentos: {classify_documents}")
        
        # Setup
        if not self.setup():
            return False
        
        # Processar emails
        try:
            print("📧 Processando emails...")
            self.processed_emails = self.gmail_client.process_emails_by_label(
                label_name=label_name,
                max_results=max_emails
            )
            
            if not self.processed_emails:
                print("⚠️  Nenhum email encontrado para processar")
                return True
            
            print(f"✅ {len(self.processed_emails)} emails processados com sucesso")
            
        except Exception as e:
            print(f"❌ Erro durante processamento: {str(e)}")
            return False
        
        # Salvar resultados
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"emails_scraped_{timestamp}.json"
        
        # Salva primeiro sem classificação
        if not self.save_results(output_file):
            return False
        
        # Classificar documentos se solicitado
        if classify_documents:
            return self.classify_documents(output_file)
        
        return True
    
    def save_results(self, output_file: str) -> bool:
        """
        Salva os resultados em arquivo JSON
        
        Args:
            output_file: Arquivo de saída
            
        Returns:
            bool: True se salvou com sucesso
        """
        try:
            # Adiciona IDs sequenciais aos emails
            for i, email in enumerate(self.processed_emails, 1):
                email.emailID = i
            
            # Converte para formato de saída
            emails_json = [email.to_dict() for email in self.processed_emails]
            
            # Adiciona metadados
            output_data = {
                "metadata": {
                    "total_emails": len(emails_json),
                    "processed_at": datetime.now().isoformat(),
                    "label_used": LABEL_NAME
                },
                "emails": emails_json
            }
            
            if save_emails_to_json(output_data, output_file):
                print(f"💾 Resultados salvos em: {output_file}")
                return True
            else:
                return False
                
        except Exception as e:
            print(f"❌ Erro ao salvar resultados: {str(e)}")
            return False
    
    def classify_documents(self, json_file: str) -> bool:
        """
        Classifica documentos usando Google Cloud Vision API
        
        Args:
            json_file: Arquivo JSON com os dados dos emails
            
        Returns:
            bool: True se classificação foi bem-sucedida
        """
        try:
            print("\n🔍 Iniciando classificação de documentos...")
            
            # Inicializa o classificador
            classifier = DocumentClassifier(test_mode=True)  # Usa modo teste por padrão
            
            # Determina arquivo de saída
            base_name = json_file.replace('.json', '')
            classified_file = f"{base_name}_classified.json"
            
            # Processa classificação
            success = classifier.process_emails_data(
                input_file=json_file,
                output_file=classified_file,
                base_path=""  # Assumindo que anexoPath já tem caminho completo
            )
            
            if success:
                print(f"✅ Documentos classificados e salvos em: {classified_file}")
                return True
            else:
                print("❌ Falha na classificação de documentos")
                return False
                
        except Exception as e:
            print(f"❌ Erro durante classificação de documentos: {str(e)}")
            return False
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do processamento
        
        Returns:
            Dict: Estatísticas do processamento
        """
        if not self.processed_emails:
            return {"total_emails": 0}
        
        total_attachments = sum(len(email.attachments) for email in self.processed_emails)
        senders = set(email.from_email for email in self.processed_emails)
        
        return {
            "total_emails": len(self.processed_emails),
            "total_attachments": total_attachments,
            "unique_senders": len(senders),
            "senders_list": list(senders),
            "avg_attachments_per_email": total_attachments / len(self.processed_emails) if self.processed_emails else 0
        }
    
    def print_summary(self):
        """Imprime um resumo do processamento"""
        stats = self.get_processing_stats()
        
        print("\n" + "="*50)
        print("📊 RESUMO DO PROCESSAMENTO")
        print("="*50)
        print(f"Emails processados: {stats['total_emails']}")
        print(f"Total de anexos: {stats['total_attachments']}")
        print(f"Remetentes únicos: {stats['unique_senders']}")
        print(f"Média de anexos por email: {stats['avg_attachments_per_email']:.1f}")
        
        if stats['senders_list']:
            print("\nRemetentes:")
            for sender in stats['senders_list']:
                print(f"  • {sender}")
        
        print("="*50)


def run_pipeline_cli():
    """Função para executar pipeline via linha de comando"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Pipeline de scraping de emails Gmail')
    parser.add_argument('--label', default=LABEL_NAME, help='Label para filtrar emails')
    parser.add_argument('--max-emails', type=int, default=100, help='Número máximo de emails')
    parser.add_argument('--output', help='Arquivo de saída JSON')
    parser.add_argument('--classify', action='store_true', default=True, help='Classificar documentos usando Vision API')
    parser.add_argument('--no-classify', action='store_false', dest='classify', help='Pular classificação de documentos')
    
    args = parser.parse_args()
    
    pipeline = EmailScrapingPipeline()
    success = pipeline.run_full_pipeline(
        label_name=args.label,
        max_emails=args.max_emails,
        output_file=args.output,
        classify_documents=args.classify
    )
    
    if success:
        pipeline.print_summary()
        print("✅ Pipeline executado com sucesso!")
    else:
        print("❌ Pipeline falhou!")
    
    return success


if __name__ == "__main__":
    run_pipeline_cli()
