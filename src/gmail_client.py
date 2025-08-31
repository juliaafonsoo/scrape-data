"""
Cliente para operações na caixa de e-mail via Gmail API
"""

import os
import base64
from typing import List, Optional, Dict, Any
from datetime import datetime

from .auth import get_gmail_service, LABEL_NAME
from .models import EmailData, EmailAttachment, LabelInfo
from .utils import (
    extract_email_username, 
    create_attachments_folder, 
    decode_base64_data,
    extract_text_from_html,
    save_attachment_to_file,
    sanitize_filename
)


class GmailClient:
    """Cliente para operações com Gmail API"""
    
    def __init__(self):
        """Inicializa o cliente Gmail"""
        self.service = get_gmail_service()
        self.labels = {}
        self._load_labels()
    
    def _load_labels(self):
        """Carrega e mapeia os labels do Gmail"""
        try:
            results = self.service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])
            
            for label in labels:
                self.labels[label['name']] = LabelInfo(
                    id=label['id'],
                    name=label['name'],
                    type=label['type']
                )
                
            print(f"Carregados {len(self.labels)} labels")
        except Exception as e:
            print(f"Erro ao carregar labels: {str(e)}")
    
    def get_label_id(self, label_name: str) -> Optional[str]:
        """
        Obtém o ID de um label pelo nome
        
        Args:
            label_name: Nome do label
            
        Returns:
            str: ID do label ou None se não encontrado
        """
        label_info = self.labels.get(label_name)
        return label_info.id if label_info else None
    
    def list_messages_by_label(self, label_name: str = LABEL_NAME, max_results: int = 100) -> List[str]:
        """
        Lista mensagens filtradas por label
        
        Args:
            label_name: Nome do label para filtrar
            max_results: Número máximo de resultados
            
        Returns:
            List[str]: Lista de IDs das mensagens
        """
        try:
            label_id = self.get_label_id(label_name)
            if not label_id:
                print(f"Label '{label_name}' não encontrado")
                return []
            
            print(f"Buscando mensagens com label '{label_name}' (ID: {label_id})")
            
            results = self.service.users().messages().list(
                userId='me',
                labelIds=[label_id],
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            message_ids = [msg['id'] for msg in messages]
            
            print(f"Encontradas {len(message_ids)} mensagens")
            return message_ids
            
        except Exception as e:
            print(f"Erro ao listar mensagens: {str(e)}")
            return []
    
    def get_message_details(self, message_id: str) -> Optional[EmailData]:
        """
        Obtém detalhes completos de uma mensagem
        
        Args:
            message_id: ID da mensagem
            
        Returns:
            EmailData: Dados da mensagem ou None se erro
        """
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            # Extrai headers
            headers = {}
            payload = message.get('payload', {})
            if 'headers' in payload:
                for header in payload['headers']:
                    headers[header['name'].lower()] = header['value']
            
            from_email = headers.get('from', 'unknown@unknown.com')
            subject = headers.get('subject', 'Sem assunto')
            
            # Extrai corpo do email
            body = self._extract_body(payload)
            
            # Extrai anexos
            attachments = self._extract_attachments(message_id, payload, from_email)
            
            return EmailData(
                from_email=from_email,
                subject=subject,
                body=body,
                attachments=attachments,
                messageId=message_id,
                date=datetime.fromtimestamp(int(message['internalDate']) / 1000)
            )
            
        except Exception as e:
            print(f"Erro ao obter detalhes da mensagem {message_id}: {str(e)}")
            return None
    
    def _extract_body(self, payload: Dict[str, Any]) -> str:
        """
        Extrai o corpo do email do payload
        
        Args:
            payload: Payload da mensagem
            
        Returns:
            str: Corpo do email em texto plano
        """
        body = ""
        
        # Se tem corpo direto
        if 'body' in payload and 'data' in payload['body']:
            body_data = payload['body']['data']
            decoded = decode_base64_data(body_data).decode('utf-8', errors='ignore')
            
            # Se é HTML, converte para texto
            if payload.get('mimeType') == 'text/html':
                body = extract_text_from_html(decoded)
            else:
                body = decoded
                
        # Se tem partes múltiplas
        elif 'parts' in payload:
            for part in payload['parts']:
                if part.get('mimeType') == 'text/plain' and 'body' in part and 'data' in part['body']:
                    body_data = part['body']['data']
                    body = decode_base64_data(body_data).decode('utf-8', errors='ignore')
                    break
                elif part.get('mimeType') == 'text/html' and 'body' in part and 'data' in part['body']:
                    body_data = part['body']['data']
                    html_content = decode_base64_data(body_data).decode('utf-8', errors='ignore')
                    body = extract_text_from_html(html_content)
                    break
                elif 'parts' in part:
                    # Recursão para partes aninhadas
                    body = self._extract_body(part)
                    if body:
                        break
        
        return body.strip()
    
    def _extract_attachments(self, message_id: str, payload: Dict[str, Any], from_email: str) -> List[EmailAttachment]:
        """
        Extrai e baixa anexos do email
        
        Args:
            message_id: ID da mensagem
            payload: Payload da mensagem
            from_email: Email do remetente
            
        Returns:
            List[EmailAttachment]: Lista de anexos
        """
        attachments = []
        email_username = extract_email_username(from_email)
        attachments_folder = create_attachments_folder(email_username)
        
        def process_part(part):
            """Processa uma parte do email recursivamente"""
            if 'parts' in part:
                for subpart in part['parts']:
                    process_part(subpart)
            
            # Verifica se é anexo
            if 'body' in part and 'attachmentId' in part['body']:
                filename = part.get('filename', 'attachment')
                if not filename:
                    # Tenta extrair nome do Content-Disposition
                    for header in part.get('headers', []):
                        if header['name'].lower() == 'content-disposition':
                            import re
                            match = re.search(r'filename="?([^"]+)"?', header['value'])
                            if match:
                                filename = match.group(1)
                                break
                
                filename = sanitize_filename(filename)
                attachment_id = part['body']['attachmentId']
                mime_type = part.get('mimeType', 'application/octet-stream')
                
                # Baixa o anexo
                attachment_path = self._download_attachment(
                    message_id, attachment_id, filename, attachments_folder
                )
                
                if attachment_path:
                    attachments.append(EmailAttachment(
                        filename=filename,
                        mimeType=mime_type,
                        anexoPath=attachment_path,
                        size=part['body'].get('size'),
                        attachmentId=attachment_id
                    ))
        
        # Processa payload recursivamente
        process_part(payload)
        
        return attachments
    
    def _download_attachment(self, message_id: str, attachment_id: str, filename: str, folder: str) -> Optional[str]:
        """
        Baixa um anexo específico
        
        Args:
            message_id: ID da mensagem
            attachment_id: ID do anexo
            filename: Nome do arquivo
            folder: Pasta de destino
            
        Returns:
            str: Caminho do arquivo baixado ou None se erro
        """
        try:
            attachment = self.service.users().messages().attachments().get(
                userId='me',
                messageId=message_id,
                id=attachment_id
            ).execute()
            
            file_data = decode_base64_data(attachment['data'])
            file_path = os.path.join(folder, filename)
            
            if save_attachment_to_file(file_data, file_path):
                print(f"Anexo baixado: {file_path}")
                return file_path
            else:
                return None
                
        except Exception as e:
            print(f"Erro ao baixar anexo {filename}: {str(e)}")
            return None
    
    def process_emails_by_label(self, label_name: str = LABEL_NAME, max_results: int = 100) -> List[EmailData]:
        """
        Processa todos os emails de um label específico
        
        Args:
            label_name: Nome do label
            max_results: Número máximo de emails para processar
            
        Returns:
            List[EmailData]: Lista de dados dos emails processados
        """
        message_ids = self.list_messages_by_label(label_name, max_results)
        emails_data = []
        
        print(f"Processando {len(message_ids)} mensagens...")
        
        for i, message_id in enumerate(message_ids):
            print(f"Processando mensagem {i+1}/{len(message_ids)}: {message_id}")
            
            email_data = self.get_message_details(message_id)
            if email_data:
                emails_data.append(email_data)
                print(f"  ✓ Processado: {email_data.subject[:50]}...")
            else:
                print(f"  ✗ Erro ao processar mensagem {message_id}")
        
        print(f"Processamento concluído: {len(emails_data)} emails processados")
        return emails_data
