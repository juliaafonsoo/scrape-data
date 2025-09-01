import json
import re
import os
import unicodedata
from typing import Dict, List, Any, Set

from google.cloud import vision
from PIL import Image

TAG_TYPES = [
    "RG",
    "CPF",
    "CNH",
    "FOTO_3X4",
    "COMPROVANTE_ENDERECO",
    "CARTAO_SUS",
    "CRM",
    "TITULO_ELEITOR",
    "DIPLOMA_MEDICINA",
    "CERTIDAO_CASAMENTO",
    "PIS",
    "CARTEIRA_TRABALHO",
    "CERTIFICADO_ACLS",
    "CERTIFICADO_ATLS",
    "CERTIFICADO_PALS",
    "CERTIFICADO_CURSO_OUTROS",
    "CERTIFICADO_ESPECIALIDADE",
    "CERTIFICADO_POS_GRADUACAO",
    "DECLARACAO_RESIDENCIA_MEDICA",
    "CURRICULO",
]

FOTO_REGEX = re.compile(r"(?i)^(?:foto[- ]?3x4|foto|3x4)\.(png|jpeg)$")

UTILITY_COMPANIES = [
    "empresa luz e forca santa maria",
    "edp es distrib de energia",
    "enel",
    "loga administracao",
    "ultragaz",
    "wk imoveis",
    "unimed vitoria",
]

KEYWORD_TAGS = {
    r"\bcpf\b": "CPF",
    r"\bcnh\b": "CNH",
    r"\bcarteira nacional de habilitacao\b": "CNH",
    r"\bregistro geral\b": "RG",
    r"\bcartao nacional de saude\b": "CARTAO_SUS",
    r"\bsistema unico de saude\b": "CARTAO_SUS",
    r"\bcrm\b": "CRM",
    r"\bconselho regional de medicina\b": "CRM",
    r"\btitulo de eleitor\b": "TITULO_ELEITOR",
    r"\bdiploma\b.*\bmedicina\b": "DIPLOMA_MEDICINA",
    r"\bcertidao de casamento\b": "CERTIDAO_CASAMENTO",
    r"\bpis\b": "PIS",
    r"\bcarteira de trabalho\b": "CARTEIRA_TRABALHO",
    r"\bacls\b": "CERTIFICADO_ACLS",
    r"\batls\b": "CERTIFICADO_ATLS",
    r"\bpals\b": "CERTIFICADO_PALS",
    r"\bcertificado\b": "CERTIFICADO_CURSO_OUTROS",
    r"\bespecialidade\b": "CERTIFICADO_ESPECIALIDADE",
    r"\bpos graduacao\b": "CERTIFICADO_POS_GRADUACAO",
    r"\bdeclaracao\b.*\bresidencia medica\b": "DECLARACAO_RESIDENCIA_MEDICA",
    r"\bcurriculo\b": "CURRICULO",
}


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFD", text)
    text = text.encode("ascii", "ignore").decode("utf-8")
    return text.lower()


def classify_from_text(text: str) -> str | None:
    for pattern, tag in KEYWORD_TAGS.items():
        if re.search(pattern, text):
            return tag
    for company in UTILITY_COMPANIES:
        if company in text:
            return "COMPROVANTE_ENDERECO"
    return None


def detect_foto_3x4(text: str, faces: List[Dict[str, Any]], image_path: str) -> bool:
    if faces and len(text) < 30:
        try:
            with Image.open(image_path) as img:
                w, h = img.size
        except Exception:
            return False
        ratio = w / h
        ratio = ratio if ratio < 1 else 1 / ratio
        if abs(ratio - 0.75) > 0.1:
            return False
        poly = faces[0]["fd_bounding_poly"]
        xs = [p["x"] for p in poly]
        ys = [p["y"] for p in poly]
        face_w = max(xs) - min(xs)
        face_h = max(ys) - min(ys)
        if face_w * face_h >= 0.2 * w * h:
            return True
    return False


def process_attachment(client: vision.ImageAnnotatorClient, attachment: Dict[str, Any]):
    path = attachment.get("anexoPath")
    if not path or not os.path.exists(path):
        return

    with open(path, "rb") as img_file:
        content = img_file.read()
    image = vision.Image(content=content)

    features = [
        vision.Feature(type_=vision.Feature.Type.LABEL_DETECTION),
        vision.Feature(type_=vision.Feature.Type.TEXT_DETECTION),
    ]
    response = client.annotate_image({"image": image, "features": features})
    labels = [label.description for label in response.label_annotations]
    text_raw = response.full_text_annotation.text or ""
    text_norm = normalize_text(text_raw)

    faces_data = []
    face_response = None
    if len(text_norm.strip()) < 10:
        face_response = client.annotate_image({
            "image": image,
            "features": [vision.Feature(type_=vision.Feature.Type.FACE_DETECTION)],
        })
    else:
        face_response = response

    if face_response and face_response.face_annotations:
        for face in face_response.face_annotations:
            poly = [{"x": v.x, "y": v.y} for v in face.fd_bounding_poly.vertices]
            faces_data.append({"fd_bounding_poly": poly})

    attachment.setdefault("annotations", {})
    attachment["annotations"].update({
        "labels": labels,
        "text": text_raw,
        "faces": faces_data,
    })
    attachment["normalized_text"] = text_norm

    tags: Set[str] = set(attachment.get("tag", []))
    if FOTO_REGEX.match(attachment.get("filename", "")):
        tags.add("FOTO_3X4")

    tag_from_text = classify_from_text(text_norm)
    if tag_from_text:
        tags.add(tag_from_text)

    if not tags and detect_foto_3x4(text_norm, faces_data, path):
        tags.add("FOTO_3X4")

    if not tags:
        tags.add("revisao manual")

    attachment["tag"] = list(tags)


def main():
    with open("emails_transformados.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    client = vision.ImageAnnotatorClient()

    for email in data.get("emails", []):
        for attachment in email.get("attachments", []):
            if attachment.get("mimeType", "").startswith("image/"):
                process_attachment(client, attachment)

    with open("emails.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
