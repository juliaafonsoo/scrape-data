"""
Utilitários para o sistema de scraping de e-mails
"""

import os
import json
import base64
import re
from typing import List, Dict, Any
from email.mime.text import MIMEText
import email
from bs4 import BeautifulSoup
from datetime import datetime


def extract_email_username(email_address: str) -> str:
    """
    Extrai o nome de usuário do email (parte antes do @)
    
    Args:
        email_address: Endereço de email completo
        
    Returns:
        str: Nome de usuário sem o domínio
    """
    if '@' in email_address:
        return email_address.split('@')[0]
    return email_address


def create_attachments_folder(email_username: str, base_path: str = "anexos-email") -> str:
    """
    Cria a pasta para armazenar anexos de um usuário específico
    
    Args:
        email_username: Nome de usuário do email
        base_path: Caminho base para os anexos
        
    Returns:
        str: Caminho completo da pasta criada
    """
    folder_path = os.path.join(base_path, email_username)
    os.makedirs(folder_path, exist_ok=True)
    return folder_path


def decode_base64_data(data: str) -> bytes:
    """
    Decodifica dados em base64 URL-safe
    
    Args:
        data: String em base64 URL-safe
        
    Returns:
        bytes: Dados decodificados
    """
    # Adiciona padding se necessário
    missing_padding = len(data) % 4
    if missing_padding:
        data += '=' * (4 - missing_padding)
    
    # Substitui caracteres URL-safe
    data = data.replace('-', '+').replace('_', '/')
    
    return base64.b64decode(data)


def extract_text_from_html(html_content: str) -> str:
    """
    Extrai texto plano de conteúdo HTML
    
    Args:
        html_content: Conteúdo HTML
        
    Returns:
        str: Texto plano extraído
    """
    if not html_content:
        return ""
    
    soup = BeautifulSoup(html_content, 'html.parser')
    # Remove scripts e styles
    for script in soup(["script", "style"]):
        script.decompose()
    
    # Extrai texto
    text = soup.get_text()
    
    # Limpa espaços extras
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = ' '.join(chunk for chunk in chunks if chunk)
    
    return text


def save_attachment_to_file(attachment_data: bytes, file_path: str) -> bool:
    """
    Salva dados de anexo em arquivo
    
    Args:
        attachment_data: Dados binários do anexo
        file_path: Caminho onde salvar o arquivo
        
    Returns:
        bool: True se salvou com sucesso, False caso contrário
    """
    try:
        # Cria diretório se não existir
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'wb') as f:
            f.write(attachment_data)
        
        return True
    except Exception as e:
        print(f"Erro ao salvar anexo {file_path}: {str(e)}")
        return False


def sanitize_filename(filename: str) -> str:
    """
    Remove caracteres inválidos do nome do arquivo
    
    Args:
        filename: Nome original do arquivo
        
    Returns:
        str: Nome do arquivo sanitizado
    """
    # Remove caracteres perigosos
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove espaços múltiplos
    filename = re.sub(r'\s+', ' ', filename).strip()
    
    # Garante que não é muito longo
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    
    return filename


def save_emails_to_json(emails_data: List[Dict[str, Any]], output_file: str = "emails_data.json") -> bool:
    """
    Salva lista de emails em arquivo JSON
    
    Args:
        emails_data: Lista de dados de emails ou dicionário com metadados
        output_file: Arquivo de saída
        
    Returns:
        bool: True se salvou com sucesso, False caso contrário
    """
    try:
        # Se é um dicionário com metadados, salva diretamente
        if isinstance(emails_data, dict):
            data_to_save = emails_data
        else:
            # Se é uma lista, adiciona IDs e metadados
            # Adiciona emailID se não existir
            for i, email in enumerate(emails_data, 1):
                if isinstance(email, dict) and "emailID" not in email:
                    email["emailID"] = i
            
            data_to_save = {
                "metadata": {
                    "total_emails": len(emails_data),
                    "processed_at": datetime.now().isoformat()
                },
                "emails": emails_data
            }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=2)
        
        print(f"Dados salvos em {output_file}")
        return True
    except Exception as e:
        print(f"Erro ao salvar JSON: {str(e)}")
        return False


def load_emails_from_json(input_file: str) -> List[Dict[str, Any]]:
    """
    Carrega emails de arquivo JSON
    
    Args:
        input_file: Arquivo de entrada
        
    Returns:
        List[Dict]: Lista de dados de emails
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Erro ao carregar JSON: {str(e)}")
        return []
