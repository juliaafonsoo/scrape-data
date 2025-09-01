"""
Módulo de autenticação para Gmail API usando OAuth2 com variáveis de ambiente
"""

import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


# Configuração
LABEL_NAME = 'DOC-MEDICOS'

# Scopes necessários para Gmail (versão mais permissiva para desenvolvimento)
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify'
]

# Para desenvolvimento, você pode usar apenas readonly se quiser:
# SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def get_credentials_from_env():
    """
    Obtém credenciais OAuth2 das variáveis de ambiente.
    
    Returns:
        dict: Conteúdo das credenciais
    """
    credentials_content = os.environ.get('GOOGLE_CREDENTIALS_JSON')
    if not credentials_content:
        raise ValueError(
            "Variável de ambiente GOOGLE_CREDENTIALS_JSON não encontrada. "
            "Configure-a com o conteúdo do arquivo credentials.json"
        )
    
    try:
        return json.loads(credentials_content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Erro ao decodificar GOOGLE_CREDENTIALS_JSON: {e}")


def get_token_from_env():
    """
    Obtém token OAuth2 das variáveis de ambiente.
    
    Returns:
        dict: Conteúdo do token (sem o campo expiry)
    """
    token_content = os.environ.get('GOOGLE_TOKEN_JSON')
    if not token_content:
        return None
    
    try:
        token_data = json.loads(token_content)
        # Remove o campo expiry se existir - deixa o Google lidar com isso
        if 'expiry' in token_data:
            del token_data['expiry']
        return token_data
    except json.JSONDecodeError as e:
        raise ValueError(f"Erro ao decodificar GOOGLE_TOKEN_JSON: {e}")


def save_token_to_env(credentials):
    """
    Salva o token atualizado na variável de ambiente (sem expiry).
    
    Args:
        credentials: Credenciais do Google
    """
    token_data = json.loads(credentials.to_json())
    # Remove o campo expiry se existir - deixa o Google lidar com isso
    if 'expiry' in token_data:
        del token_data['expiry']
    
    # Nota: Em produção, você deve usar um sistema seguro para atualizar
    # variáveis de ambiente. Este é apenas um exemplo.
    print("💾 Token atualizado. Em produção, atualize a variável GOOGLE_TOKEN_JSON.")
    print(f"Novo token (sem expiry): {json.dumps(token_data)}")


def get_gmail_credentials():
    """
    Cria e retorna credenciais autenticadas para Gmail API usando OAuth2 com variáveis de ambiente.
    
    Returns:
        google.oauth2.credentials.Credentials: Credenciais autenticadas
    """
    creds = None
    
    # Verifica se já existe token nas variáveis de ambiente
    token_data = get_token_from_env()
    if token_data:
        print("📁 Carregando token das variáveis de ambiente...")
        creds = Credentials.from_authorized_user_info(token_data, SCOPES)
    
    # Se não há credenciais válidas disponíveis
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Renovando token expirado...")
            creds.refresh(Request())
            save_token_to_env(creds)
        else:
            # Obtém credenciais das variáveis de ambiente
            credentials_data = get_credentials_from_env()
            
            print("🔐 Iniciando fluxo de autenticação OAuth2...")
            print("Uma janela do navegador será aberta para autorização.")
            
            # Inicia o fluxo OAuth2
            flow = InstalledAppFlow.from_client_config(
                credentials_data, SCOPES)
            creds = flow.run_local_server(port=0)
            
            print("✅ Autorização concluída!")
            save_token_to_env(creds)
    
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
        save_token_to_env(credentials)
    
    return credentials


def validate_authentication():
    """
    Valida se a autenticação está funcionando corretamente.
    
    Returns:
        bool: True se a autenticação está funcionando, False caso contrário
    """
    try:
        print("🔐 Validando autenticação OAuth2...")
        print("   Usando variáveis de ambiente para credenciais")
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
        print("1. Verificar se a variável GOOGLE_CREDENTIALS_JSON está configurada")
        print("2. Verificar se a variável GOOGLE_TOKEN_JSON está configurada")
        print("3. Verificar se os scopes estão corretos no Google Cloud Console")
        print("4. Verificar se a API Gmail está habilitada no projeto")
        return False


def check_oauth_info():
    """
    Mostra informações do OAuth2 para debug
    """
    try:
        print("📋 Informações do OAuth2:")
        
        # Informações das variáveis de ambiente
        credentials_env = os.environ.get('GOOGLE_CREDENTIALS_JSON')
        if credentials_env:
            try:
                cred_info = json.loads(credentials_env)
                installed = cred_info.get('installed', {})
                print(f"   Project ID: {installed.get('project_id')}")
                print(f"   Client ID: {installed.get('client_id')}")
                print(f"   Auth URI: {installed.get('auth_uri')}")
                print("   ✅ GOOGLE_CREDENTIALS_JSON configurada")
            except json.JSONDecodeError:
                print("   ❌ GOOGLE_CREDENTIALS_JSON mal formada")
        else:
            print("   ❌ Variável GOOGLE_CREDENTIALS_JSON não encontrada")
        
        # Informações do token
        token_env = os.environ.get('GOOGLE_TOKEN_JSON')
        if token_env:
            try:
                token_info = json.loads(token_env)
                print(f"   Token válido: {'✅' if token_info.get('token') else '❌'}")
                print(f"   Refresh token: {'✅' if token_info.get('refresh_token') else '❌'}")
                print("   ✅ GOOGLE_TOKEN_JSON configurada")
                # Não mostra mais expiry pois foi removido
                print("   ℹ️  Campo 'expiry' removido - Google gerencia automaticamente")
            except json.JSONDecodeError:
                print("   ❌ GOOGLE_TOKEN_JSON mal formada")
        else:
            print("   ❌ Variável GOOGLE_TOKEN_JSON não encontrada")
            
    except Exception as e:
        print(f"Erro ao ler informações OAuth2: {e}")


def reset_authentication():
    """
    Remove o token das variáveis de ambiente para forçar nova autenticação
    """
    try:
        if os.environ.get('GOOGLE_TOKEN_JSON'):
            print("ℹ️  Para resetar a autenticação, remova a variável GOOGLE_TOKEN_JSON.")
            print("   Em seguida, execute novamente o programa para nova autenticação.")
        else:
            print("ℹ️  Variável GOOGLE_TOKEN_JSON não encontrada. Nova autenticação será necessária.")
    except Exception as e:
        print(f"Erro ao verificar token: {e}")
