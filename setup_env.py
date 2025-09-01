#!/usr/bin/env python3
"""
Script para configurar variáveis de ambiente com credenciais Google
"""

import json
import os

def setup_environment_variables():
    """
    Configura as variáveis de ambiente com base nos arquivos credentials.json e token.json
    """
    print("🔧 Configurando variáveis de ambiente para Google OAuth2...")
    
    # Lê credentials.json
    credentials_file = 'credentials.json'
    if os.path.exists(credentials_file):
        with open(credentials_file, 'r') as f:
            credentials_content = f.read().strip()
        
        print(f"✅ Lido {credentials_file}")
        print("📋 Configure a variável de ambiente:")
        print(f"export GOOGLE_CREDENTIALS_JSON='{credentials_content}'")
        print()
    else:
        print(f"❌ Arquivo {credentials_file} não encontrado")
    
    # Lê token.json e remove expiry
    token_file = 'token.json'
    if os.path.exists(token_file):
        with open(token_file, 'r') as f:
            token_data = json.load(f)
        
        # Remove o campo expiry se existir
        if 'expiry' in token_data:
            del token_data['expiry']
            print("ℹ️  Campo 'expiry' removido do token")
        
        token_content = json.dumps(token_data)
        
        print(f"✅ Lido {token_file}")
        print("📋 Configure a variável de ambiente:")
        print(f"export GOOGLE_TOKEN_JSON='{token_content}'")
        print()
    else:
        print(f"❌ Arquivo {token_file} não encontrado")
    
    print("🚀 Para usar no terminal, execute:")
    print("source <(python3 setup_env.py)")
    print()
    print("🐳 Para Docker, adicione no Dockerfile:")
    print("ENV GOOGLE_CREDENTIALS_JSON='...'")
    print("ENV GOOGLE_TOKEN_JSON='...'")

if __name__ == "__main__":
    setup_environment_variables()
