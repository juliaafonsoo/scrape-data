#!/usr/bin/env python3
"""
Script standalone para classificar documentos médicos do arquivo emails_data.json
"""

import sys
import os

# Adiciona o diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.document_classifier import DocumentClassifier


def main():
    """Função principal"""
    print("🚀 Iniciando classificação de documentos médicos...")
    
    # Argumentos via linha de comando
    import argparse
    parser = argparse.ArgumentParser(description='Classificador de documentos médicos')
    parser.add_argument('--test-mode', action='store_true', help='Executa em modo de teste sem chamar a API')
    parser.add_argument('--input', default='emails_data.json', help='Arquivo JSON de entrada')
    parser.add_argument('--output', default='emails.json', help='Arquivo JSON de saída')
    
    args = parser.parse_args()
    
    # Verifica se arquivo de entrada existe
    if not os.path.exists(args.input):
        print(f"❌ Arquivo não encontrado: {args.input}")
        return False
    
    # Inicializa classificador
    classifier = DocumentClassifier(test_mode=args.test_mode)
    
    # Processa classificação
    success = classifier.process_emails_data(
        input_file=args.input,
        output_file=args.output,
        base_path=""  # anexoPath já contém caminho completo
    )
    
    if success:
        print(f"✅ Classificação concluída! Arquivo gerado: {args.output}")
    else:
        print("❌ Falha na classificação!")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
