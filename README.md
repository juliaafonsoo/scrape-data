scrape-data

Integração entre dados desestruturados e a necessidade de jogar tudo num formato semi-estruturado (tipo JSON/dicionário). A ideia é montar uma pipeline que varre os e-mails com label "DOC-MEDICOS", organiza os metadados básicos e já deixa os anexos classificados.

Arquitetura:
1. Autenticação no Gmail
    * Usa a API oficial do Gmail (Google API Client).
    * Autenticação via OAuth 2.0 (token.json salvo para não pedir login toda hora).
2. Busca por e-mails com label
    * A API permite listar mensagens filtradas por labelId.
    * Como você já tem o label "ficha médicos", é só mapear o label para o ID.
3. Iteração por e-mail
    * Para cada e-mail:
        * Extrair from, to, subject, body (plain text e/ou HTML convertido).
        * Listar anexos.
4. Download dos anexos
    * Para cada anexo:
        * Pega o filename, mimeType (já te dá se é imagem, pdf etc.).
        * Decodifica o conteúdo base64.
5. Armazenamento dos anexos no Google Drive
    * Envia cada anexo pro Google Drive via API.
    * Retorna a URL pública
6. Estruturação em dicionário {
7.     "from": "exemplo@hospital.com",
8.     "subject": "Ficha cadastral",
9.     "body": "Texto do corpo do e-mail...",
10.     "attachments": [
11.         {
12.             "filename": "ficha.pdf",
13.             "mimeType": "application/pdf",
14.             "drive_link": "https://drive.google.com/file/..."
15.         },
16.         {
17.             "filename": "foto.png",
18.             "mimeType": "image/png",
19.             "drive_link": "https://drive.google.com/file/..."
20.         }
21.     ]
22. }
23. 

⚙️ Tecnologias
* Python + google-api-python-client (para Gmail e Drive).
* oauthlib ou google-auth para autenticação.
* Armazenamento em JSON local.

🚀Fluxo no Python
1. Autentica e cria service_gmail e service_drive.
2. Lista mensagens com service_gmail.users().messages().list(userId='me', labelIds=['LabelIdFichaMedicos']).
3. Para cada mensagem:
    * Busca detalhes com .get(userId='me', id=message_id, format='full').
    * Extrai headers (From, Subject).
    * Extrai body (plain).
    * Para cada attachment: baixa conteúdo, salva em Drive (upload), pega link.
    * Monta o dicionário.

Next steps: extração das informações da ficha (nome do médico, CRM, especialidade, etc.) -> AgentQL API se a ficha estiver só em imagem, LLM API se estiver em texto.
