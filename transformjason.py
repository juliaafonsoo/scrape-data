import json

# Carregar o JSON original (substitua pelo seu caminho ou objeto JSON direto)
with open("/Users/juliaafonso/code/scrape-data/emails_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

email_id = 1
attachment_id = 1

# Processar cada e-mail
for email in data.get("emails", []):
    email["emailID"] = email_id
    email_id += 1

    # Processar cada anexo
    for attachment in email.get("attachments", []):
        attachment["attachmentID"] = attachment_id
        attachment["tag"] = []
        attachment_id += 1

# (Opcional) Salvar o resultado em novo arquivo JSON
with open("emails_transformados.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
