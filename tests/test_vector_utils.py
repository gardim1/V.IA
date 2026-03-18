from vector_utils import inferir_categoria


def test_faq_formacao_is_categorized_by_content():
    content = (
        "Pergunta frequente: Qual a formacao do Vinicius?\n\n"
        "Resposta direta:\n"
        "Vinicius cursa Engenharia de Software na FIAP."
    )

    assert inferir_categoria("faq_recrutador.txt", content) == "FORMACAO"


def test_faq_objetivos_is_categorized_by_content():
    content = (
        "Pergunta frequente: Onde o Vinicius quer estar em 5 anos?\n\n"
        "Resposta direta:\n"
        "Ele pretende estar consolidado na area de tecnologia."
    )

    assert inferir_categoria("faq_recrutador.txt", content) == "OBJETIVOS"
