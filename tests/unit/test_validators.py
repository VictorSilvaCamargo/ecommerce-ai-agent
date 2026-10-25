import pytest
from hypothesis import given, strategies as st
from atendente.domain.validators import (
    validate_cpf,
    validate_cnpj,
    validate_document,
    DocumentType,
    clean_digits
)


@pytest.mark.unit
def test_clean_digits() -> None:
    assert clean_digits("123.456.789-00") == "12345678900"
    assert clean_digits("12.345.678/0001-95") == "12345678000195"
    assert clean_digits("abc123def") == "123"


@pytest.mark.unit
def test_validate_cpf_valid() -> None:
    # Known valid CPFs for test
    assert validate_cpf("52998224725") is True
    assert validate_cpf("529.982.247-25") is True
    assert validate_cpf("00000000191") is True


@pytest.mark.unit
def test_validate_cpf_invalid_repeated_digits() -> None:
    for digit in "0123456789":
        assert validate_cpf(digit * 11) is False


@pytest.mark.unit
def test_validate_cpf_invalid_digits() -> None:
    assert validate_cpf("12345678901") is False
    assert validate_cpf("52998224720") is False
    assert validate_cpf("123") is False
    assert validate_cpf("123456789012") is False


@pytest.mark.unit
def test_validate_cnpj_valid() -> None:
    # Known valid CNPJs for test
    assert validate_cnpj("11222333000181") is True
    assert validate_cnpj("11.222.333/0001-81") is True
    assert validate_cnpj("00000000000191") is True


@pytest.mark.unit
def test_validate_cnpj_invalid_repeated_digits() -> None:
    for digit in "0123456789":
        assert validate_cnpj(digit * 14) is False


@pytest.mark.unit
def test_validate_cnpj_invalid_digits() -> None:
    assert validate_cnpj("11222333000180") is False
    assert validate_cnpj("123") is False
    assert validate_cnpj("112223330001819") is False


@pytest.mark.unit
def test_validate_document_routing() -> None:
    doc_type, clean_doc = validate_document("529.982.247-25")
    assert doc_type == DocumentType.CPF
    assert clean_doc == "52998224725"

    doc_type, clean_doc = validate_document("11.222.333/0001-81")
    assert doc_type == DocumentType.CNPJ
    assert clean_doc == "11222333000181"

    with pytest.raises(ValueError, match="Documento inválido"):
        validate_document("123456")


@given(st.text(min_size=0, max_size=20))
def test_property_clean_digits(s: str) -> None:
    cleaned = clean_digits(s)
    assert all(c.isdigit() for c in cleaned)
