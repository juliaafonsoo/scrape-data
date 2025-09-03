#!/usr/bin/env python3
"""
Relatório de classificação de documentos médicos
"""

import json
import sys
from collections import Counter


def generate_classification_report(json_file: str):
    """
    Gera relatório detalhado da classificação de documentos
    
    Args:
        json_file: Arquivo JSON com classificações
    """
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Coleta estatísticas
        total_emails = data['metadata']['total_emails']
        classification_stats = data['metadata'].get('classification_stats', {})
        total_images = classification_stats.get('total_images', 0)
        api_calls = classification_stats.get('api_calls', 0)
        
        # Conta tags
        tag_counter = Counter()
        emails_with_images = 0
        
        for email in data['emails']:
            has_images = False
            for attachment in email.get('attachments', []):
                if attachment.get('mimeType', '').startswith('image/'):
                    has_images = True
                    tags = attachment.get('tag', [])
                    for tag in tags:
                        tag_counter[tag] += 1
            
            if has_images:
                emails_with_images += 1
        
        # Gera relatório
        print("=" * 70)
        print("📊 RELATÓRIO DE CLASSIFICAÇÃO DE DOCUMENTOS MÉDICOS")
        print("=" * 70)
        print(f"Total de emails processados: {total_emails:,}")
        print(f"Emails com imagens: {emails_with_images:,}")
        print(f"Total de imagens classificadas: {total_images:,}")
        print(f"Chamadas à API Google Vision: {api_calls:,}")
        
        if api_calls == 0:
            print("🧪 Classificação realizada em MODO DE TESTE")
        else:
            cost_estimate = (api_calls / 1000) * 1.50
            print(f"💰 Custo estimado da API: ${cost_estimate:.2f}")
        
        print("\n📋 DISTRIBUIÇÃO POR TIPO DE DOCUMENTO:")
        print("-" * 50)
        
        # Ordena por quantidade (decrescente)
        sorted_tags = tag_counter.most_common()
        
        total_classified = sum(tag_counter.values())
        
        for tag, count in sorted_tags:
            percentage = (count / total_classified) * 100 if total_classified > 0 else 0
            
            # Emojis para cada tipo
            emoji_map = {
                'FOTO_3X4': '📸',
                'RG': '🆔',
                'CPF': '📄',
                'CARTAO_SUS': '🏥',
                'CRM': '👨‍⚕️',
                'CNH': '🚗',
                'COMPROVANTE_ENDERECO': '🏠',
                'DIPLOMA_MEDICINA': '🎓',
                'CERTIFICADO_ACLS': '🚑',
                'CERTIFICADO_ATLS': '🚨',
                'CERTIFICADO_PALS': '👶',
                'CERTIFICADO_ESPECIALIDADE': '🏆',
                'CERTIFICADO_POS_GRADUACAO': '📚',
                'CURRICULO': '📝',
                'REVISAO_MANUAL': '⚠️'
            }
            
            emoji = emoji_map.get(tag, '📋')
            print(f"{emoji} {tag:<25} {count:>3} ({percentage:>5.1f}%)")
        
        print("-" * 50)
        print(f"📊 Total classificado: {total_classified:,}")
        
        # Análise de eficácia
        revisao_manual = tag_counter.get('REVISAO_MANUAL', 0)
        if total_classified > 0:
            eficacia = ((total_classified - revisao_manual) / total_classified) * 100
            print(f"✅ Eficácia da classificação: {eficacia:.1f}%")
        
        print("\n🎯 CLASSIFICAÇÕES MAIS COMUNS:")
        print("-" * 30)
        top_5 = sorted_tags[:5]
        for i, (tag, count) in enumerate(top_5, 1):
            print(f"{i}. {tag}: {count}")
        
        print("\n💡 RECOMENDAÇÕES:")
        print("-" * 20)
        
        if revisao_manual > total_classified * 0.3:
            print("• Alto número de documentos para revisão manual")
            print("  Considere melhorar as heurísticas de classificação")
        
        if tag_counter.get('FOTO_3X4', 0) > 0:
            print(f"• {tag_counter['FOTO_3X4']} fotos 3x4 identificadas com sucesso")
        
        if api_calls == 0:
            print("• Para melhor precisão, execute com Google Cloud Vision API")
            print("  (remove --test-mode e configure credenciais)")
        
        print("=" * 70)
        
    except FileNotFoundError:
        print(f"❌ Arquivo não encontrado: {json_file}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"❌ Erro ao ler arquivo JSON: {json_file}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")
        sys.exit(1)


def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Relatório de classificação de documentos')
    parser.add_argument('--file', default='emails.json', help='Arquivo JSON classificado')
    
    args = parser.parse_args()
    
    generate_classification_report(args.file)


if __name__ == "__main__":
    main()
