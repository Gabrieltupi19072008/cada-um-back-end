# lei_cotas.py - Cálculo da cota legal de vagas para PcD (Art. 93 da Lei nº 8.213/91)
#
# Faixas oficiais, por total de empregados da empresa:
#   menos de 100          -> isenta (lei não se aplica)
#   100 a 200 empregados   -> 2%
#   201 a 500 empregados   -> 3%
#   501 a 1000 empregados  -> 4%
#   mais de 1000 empregados -> 5%


def calcular_cota_legal(total_funcionarios: int | None) -> tuple[float, int]:
    """Retorna (percentual_exigido, vagas_necessarias) a partir do total de empregados."""
    if not total_funcionarios or total_funcionarios < 100:
        return 0.0, 0

    if total_funcionarios <= 200:
        percentual = 2.0
    elif total_funcionarios <= 500:
        percentual = 3.0
    elif total_funcionarios <= 1000:
        percentual = 4.0
    else:
        percentual = 5.0

    vagas_necessarias = round(total_funcionarios * percentual / 100)
    return percentual, vagas_necessarias
