"""Conversão segura de entrada monetária, independente de apresentação."""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

CENT = Decimal("0.01")


def parse_decimal(value: str) -> Decimal:
    """Converte entrada textual canônica ou pt-BR sem utilizar float."""
    clean = value.strip().replace("R$", "").replace(" ", "")
    if not clean:
        raise ValueError("Informe um valor.")
    if "," in clean:
        clean = clean.replace(".", "").replace(",", ".")
    try:
        number = Decimal(clean)
    except InvalidOperation as error:
        raise ValueError("Informe um valor monetário válido.") from error
    if not number.is_finite():
        raise ValueError("Informe um valor monetário válido.")
    rounded = number.quantize(CENT, rounding=ROUND_HALF_UP)
    if rounded != number:
        raise ValueError("Use no máximo duas casas decimais.")
    return rounded
