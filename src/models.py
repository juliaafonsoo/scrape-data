"""
Modelos de dados para o sistema de scraping de e-mails
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class EmailAttachment:
    """Representa um anexo de e-mail"""
    filename: str
    mimeType: str
    anexoPath: str
    size: Optional[int] = None
    attachmentId: Optional[str] = None


@dataclass
class EmailData:
    """Representa os dados extraídos de um e-mail"""
    from_email: str
    subject: str
    body: str
    attachments: List[EmailAttachment]
    emailID: Optional[int] = None
    messageId: Optional[str] = None
    date: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        """Converte para dicionário para serialização JSON"""
        result = {
            "from": self.from_email,
            "subject": self.subject,
            "body": self.body,
            "attachments": [
                {
                    "filename": att.filename,
                    "mimeType": att.mimeType,
                    "anexoPath": att.anexoPath
                }
                for att in self.attachments
            ]
        }
        
        # Adiciona emailID no início se existir
        if self.emailID is not None:
            result = {"emailID": self.emailID, **result}
        
        return result


@dataclass
class LabelInfo:
    """Informações sobre um label do Gmail"""
    id: str
    name: str
    type: str
