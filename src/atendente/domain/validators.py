import re
from enum import StrEnum


class DocumentType(StrEnum):
    CPF = "CPF"
    CNPJ = "CNPJ"


def clean_digits(value: str) -> str:
    """Extrai somente os caracteres numéricos da string."""
    return re.sub(r"\D", "", value)


def validate_cpf(cpf: str) -> bool:
    """
    Valida um CPF brasileiro segundo o algoritmo oficial da Receita Federal.
    Aceita com ou sem formatação (pontos e traço).
    """
    digits = clean_digits(cpf)
    if len(digits) != 11:
        return False

    # CPFs com todos os dígitos iguais são considerados inválidos
    if digits == digits[0] * 11:
        return False

    # Primeiro dígito verificador
    sum_1 = sum(int(digits[i]) * (10 - i) for i in range(9))
    rem_1 = 11 - (sum_1 % 11)
    digit_1 = 0 if rem_1 >= 10 else rem_1
    if int(digits[9]) != digit_1:
        return False

    # Segundo dígito verificador
    sum_2 = sum(int(digits[i]) * (11 - i) for i in range(10))
    rem_2 = 11 - (sum_2 % 11)
    digit_2 = 0 if rem_2 >= 10 else rem_2
    return int(digits[10]) == digit_2


def validate_cnpj(cnpj: str) -> bool:
    """
    Valida um CNPJ brasileiro segundo o algoritmo oficial da Receita Federal.
    Aceita com ou sem formatação.
    """
    digits = clean_digits(cnpj)
    if len(digits) != 14:
        return False

    # CNPJs com todos os dígitos iguais são considerados inválidos
    if digits == digits[0] * 14:
        return False

    # Primeiro dígito verificador
    weights_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    sum_1 = sum(int(digits[i]) * weights_1[i] for i in range(12))
    rem_1 = sum_1 % 11
    digit_1 = 0 if rem_1 < 2 else 11 - rem_1
    if int(digits[12]) != digit_1:
        return False

    # Segundo dígito verificador
    weights_2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    sum_2 = sum(int(digits[i]) * weights_2[i] for i in range(13))
    rem_2 = sum_2 % 11
    digit_2 = 0 if rem_2 < 2 else 11 - rem_2
    return int(digits[13]) == digit_2


def validate_document(doc: str) -> tuple[DocumentType, str]:
    """
    Identifica o tipo de documento (CPF ou CNPJ) e valida sua integridade.
    Retorna uma tupla (DocumentType, digitos_limpos).
    Lança ValueError se for inválido.
    """
    digits = clean_digits(doc)
    if len(digits) == 11 and validate_cpf(digits):
        return DocumentType.CPF, digits
    if len(digits) == 14 and validate_cnpj(digits):
        return DocumentType.CNPJ, digits
    raise ValueError(f"Documento inválido ou com formato desconhecido: '{doc}'")
