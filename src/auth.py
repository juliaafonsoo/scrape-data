"""
Módulo de autenticação para Gmail API usando OAuth2
"""

import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


# Configuração
CREDENTIALS_FILE = 'credentials.json'  # OAuth2 credentials
TOKEN_FILE = 'token.json'              # Arquivo para salvar token
LABEL_NAME = 'DOC-MEDICOS'

# Scopes necessários para Gmail (versão mais permissiva para desenvolvimento)
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify'
]

# Para desenvolvimento, você pode usar apenas readonly se quiser:
# SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def get_gmail_credentials():
    """
    Cria e retorna credenciais autenticadas para Gmail API usando OAuth2.
    
    Returns:
        google.oauth2.credentials.Credentials: Credenciais autenticadas
    """
    creds = None
    
    # Verifica se já existe token salvo
    if os.path.exists(TOKEN_FILE):
        print("📁 Carregando token existente...")
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    # Se não há credenciais válidas disponíveis
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Renovando token expirado...")
            creds.refresh(Request())
        else:
            # Verifica se o arquivo de credenciais existe
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"Arquivo {CREDENTIALS_FILE} não encontrado. "
                    "Baixe as credenciais OAuth2 do Google Cloud Console."
                )
            
            print("🔐 Iniciando fluxo de autenticação OAuth2...")
            print("Uma janela do navegador será aberta para autorização.")
            
            # Inicia o fluxo OAuth2
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
            
            print("✅ Autorização concluída!")
        
        # Salva as credenciais para uso futuro
        print("💾 Salvando token para uso futuro...")
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    
    return creds


def get_gmail_service():
    """
    Cria e retorna um serviço autenticado do Gmail API.
    
    Returns:
        googleapiclient.discovery.Resource: Serviço Gmail API
    """
    credentials = get_gmail_credentials()
    service = build('gmail', 'v1', credentials=credentials)
    return service


def refresh_credentials(credentials):
    """
    Atualiza as credenciais se necessário.
    
    Args:
        credentials: Credenciais do Google
        
    Returns:
        google.oauth2.credentials.Credentials: Credenciais atualizadas
    """
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        
        # Salva token atualizado
        with open(TOKEN_FILE, 'w') as token:
            token.write(credentials.to_json())
    
    return credentials


def validate_authentication():
    """
    Valida se a autenticação está funcionando corretamente.
    
    Returns:
        bool: True se a autenticação está funcionando, False caso contrário
    """
    try:
        print("🔐 Validando autenticação OAuth2...")
        print(f"   Credentials File: {CREDENTIALS_FILE}")
        print(f"   Token File: {TOKEN_FILE}")
        print(f"   Scopes: {SCOPES}")
        
        service = get_gmail_service()
        
        # Tenta fazer uma requisição simples para validar
        profile = service.users().getProfile(userId='me').execute()
        email = profile.get('emailAddress')
        
        print(f"✅ Autenticação bem-sucedida para: {email}")
        
        # Mostra informações adicionais
        total_messages = profile.get('messagesTotal', 0)
        total_threads = profile.get('threadsTotal', 0)
        
        print(f"📊 Informações da conta:")
        print(f"   Total de mensagens: {total_messages}")
        print(f"   Total de threads: {total_threads}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na autenticação: {str(e)}")
        print("\n🔧 Possíveis soluções:")
        print("1. Verificar se o arquivo credentials.json está presente")
        print("2. Excluir token.json e refazer a autenticação")
        print("3. Verificar se os scopes estão corretos no Google Cloud Console")
        print("4. Verificar se a API Gmail está habilitada no projeto")
        return False


def check_oauth_info():
    """
    Mostra informações do OAuth2 para debug
    """
    try:
        print("📋 Informações do OAuth2:")
        
        # Informações do credentials.json
        if os.path.exists(CREDENTIALS_FILE):
            with open(CREDENTIALS_FILE, 'r') as f:
                cred_info = json.load(f)
            
            installed = cred_info.get('installed', {})
            print(f"   Project ID: {installed.get('project_id')}")
            print(f"   Client ID: {installed.get('client_id')}")
            print(f"   Auth URI: {installed.get('auth_uri')}")
        else:
            print(f"   ❌ Arquivo {CREDENTIALS_FILE} não encontrado")
        
        # Informações do token.json
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'r') as f:
                token_info = json.load(f)
            
            print(f"   Token válido: {'✅' if token_info.get('token') else '❌'}")
            print(f"   Refresh token: {'✅' if token_info.get('refresh_token') else '❌'}")
            print(f"   Expiry: {token_info.get('expiry', 'N/A')}")
        else:
            print(f"   Token: ❌ Arquivo {TOKEN_FILE} não encontrado")
            
    except Exception as e:
        print(f"Erro ao ler informações OAuth2: {e}")


def reset_authentication():
    """
    Remove o token salvo para forçar nova autenticação
    """
    try:
        if os.path.exists(TOKEN_FILE):
            os.remove(TOKEN_FILE)
            print(f"✅ Token removido. Nova autenticação será necessária.")
        else:
            print("ℹ️  Nenhum token encontrado para remover.")
    except Exception as e:
        print(f"Erro ao remover token: {e}")
