import os
import pytest
import requests

from crawl_conference import (
    NIPSPosterAbstractRetrieval,
    NIPSRetrieval,
    TranslatorEN2ZH,
    reinforcement_learning_filter,
)


@pytest.fixture
def nips_main_html_content():
    with open(
        os.path.join(os.path.abspath(os.getcwd()), "tests/assets/nips_2023.html"),
        "r",
        encoding="utf-8",
    ) as f:
        return f.read()


@pytest.fixture
def nips_poster_html_content():
    with open(
        os.path.join(os.path.abspath(os.getcwd()), "tests/assets/poster.html"),
        "r",
        encoding="utf-8",
    ) as f:
        return f.read()


@pytest.fixture
def nips_poster_html_content_2():
    with open(
        os.path.join(os.path.abspath(os.getcwd()), "tests/assets/poster2.html"),
        "r",
        encoding="utf-8",
    ) as f:
        return f.read()


def test_given_nips_main_page_when_retrieval_then_get_page_info(nips_main_html_content):
    page_info = NIPSRetrieval().retrieval(nips_main_html_content, lambda text: True)
    assert page_info is not None
    assert page_info.talks is not None
    assert page_info.expo_workshops is not None
    assert page_info.workshops is not None
    assert page_info.competitions is not None
    assert page_info.posters is not None


def test_given_nips_main_page_when_retrieval_reinforcement_learning_then_get_page_info(
    nips_main_html_content,
):
    page_info = NIPSRetrieval().retrieval(
        nips_main_html_content, reinforcement_learning_filter
    )
    assert page_info is not None
    assert page_info.talks is not None
    assert page_info.expo_workshops is not None
    assert page_info.workshops is not None
    assert page_info.competitions is not None
    assert page_info.posters is not None
    for item in page_info.talks:
        assert reinforcement_learning_filter(item.title)
    for item in page_info.expo_workshops:
        assert reinforcement_learning_filter(item.title)
    for item in page_info.workshops:
        assert reinforcement_learning_filter(item.title)
    for item in page_info.competitions:
        assert reinforcement_learning_filter(item.title)
    for item in page_info.posters:
        assert reinforcement_learning_filter(item.title)


def test_given_nips_poster_page_when_retrieval_then_get_poster_item(
    nips_poster_html_content, nips_poster_html_content_2
):
    nips_poster_item = NIPSPosterAbstractRetrieval().retrieval(nips_poster_html_content)
    assert nips_poster_item.abstract is not None
    assert nips_poster_item.author is not None

    nips_poster_item = NIPSPosterAbstractRetrieval().retrieval(
        nips_poster_html_content_2
    )
    assert nips_poster_item.abstract is not None
    assert nips_poster_item.author is not None


def test_given_nips_main_page_url_when_request_then_get_html_content():
    response = requests.get("https://nips.cc/virtual/2023/calendar")
    assert response.status_code == 200
    assert response.text is not None


def test_given_nips_poster_url_when_request_then_get_html_content():
    response = requests.get("https://nips.cc/virtual/2023/poster/70701")
    assert response.status_code == 200
    assert response.text is not None


def is_english(str):
    try:
        str.encode(encoding="utf-8").decode("ascii")
    except UnicodeDecodeError:
        return False
    else:
        return True


def is_chinese(str):
    try:
        str.encode(encoding="utf-8").decode("ascii")
    except UnicodeDecodeError:
        return True
    else:
        return False


def test_given_string_when_check_language_then_return_true_or_false():
    assert is_english("hello") == True
    assert is_english("你好") == False
    assert is_chinese("hello") == False
    assert is_chinese("你好") == True


def test_given_en_string_when_translate_to_zh_then_return_zh_string():
    assert is_chinese(TranslatorEN2ZH().translate("hello")) == True
