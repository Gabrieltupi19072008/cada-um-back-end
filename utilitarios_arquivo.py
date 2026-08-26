# utilitarios_arquivo.py - Validacao/decodificacao de arquivos enviados como data URI
# (base64), compartilhado entre rotas de candidato (upload) e empresa (download).

import base64
import re

from fastapi import HTTPException, status

_PADRAO_DATA_URI_CURRICULO = re.compile(
    r"^data:(application/pdf|application/msword|"
    r"application/vnd\.openxmlformats-officedocument\.wordprocessingml\.document);base64,"
)
TAMANHO_MAXIMO_CURRICULO_BYTES = 4 * 1024 * 1024  # 4 MB


def validar_e_decodificar_curriculo(data_uri: str) -> tuple[bytes, str]:
    """Valida o formato/tamanho de um curriculo enviado como data URI e retorna
    (bytes_do_arquivo, mime_type). Levanta HTTPException 400 se invalido."""
    correspondencia = _PADRAO_DATA_URI_CURRICULO.match(data_uri)
    if not correspondencia:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de arquivo inválido. Envie um PDF ou Word (.doc/.docx).",
        )

    mime_tipo = correspondencia.group(1)
    parte_base64 = data_uri.split(",", 1)[1]
    try:
        bruto = base64.b64decode(parte_base64, validate=True)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Arquivo corrompido")

    if len(bruto) > TAMANHO_MAXIMO_CURRICULO_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Arquivo muito grande (máximo 4 MB). Tente um arquivo menor.",
        )

    return bruto, mime_tipo
