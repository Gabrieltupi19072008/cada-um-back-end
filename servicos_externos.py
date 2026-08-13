# servicos_externos.py - Integrações com APIs públicas de terceiros

import re
import requests


def consultar_cnpj_receita(cnpj: str) -> dict | None:
    """Consulta dados oficiais do CNPJ na BrasilAPI (gratuita, sem chave).
    Retorna None se o CNPJ não existir ou a API estiver fora do ar -- nunca
    lança exceção, pra não travar a tela de aprovação do Admin."""
    cnpj_limpo = re.sub(r"\D", "", cnpj or "")
    if len(cnpj_limpo) != 14:
        return None

    try:
        resposta = requests.get(f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_limpo}", timeout=6)
        if resposta.status_code != 200:
            return None
        dados = resposta.json()
        return {
            "razao_social": dados.get("razao_social"),
            "nome_fantasia": dados.get("nome_fantasia"),
            "situacao_cadastral": dados.get("descricao_situacao_cadastral"),
            "data_abertura": dados.get("data_inicio_atividade"),
        }
    except requests.RequestException:
        return None
