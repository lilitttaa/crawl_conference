import json
from typing import Callable, Dict, List
from g4f.models import Model, RetryProvider, Liaobots
from bs4 import BeautifulSoup
from g4f.client import Client
import requests


def reinforcement_learning_filter(text: str) -> bool:
    return "reinforcement learning" in text.lower()


class NIPSItem:
    def __init__(self, url: str, title: str) -> None:
        self.url = url
        self.title = title

    def __str__(self) -> str:
        return f"url:[{self.url}]-title[{self.title}]"

    def to_dict(self) -> dict:
        return {"url": self.url, "title": self.title}


class NIPSPageInfo:
    def __init__(self) -> None:
        self.talks: List[NIPSItem] = []
        self.expo_workshops: List[NIPSItem] = []
        self.workshops: List[NIPSItem] = []
        self.competitions: List[NIPSItem] = []
        self.posters: List[NIPSItem] = []

    def to_dict(self) -> dict:
        return {
            "talks": [item.to_dict() for item in self.talks],
            "expo_workshops": [item.to_dict() for item in self.expo_workshops],
            "workshops": [item.to_dict() for item in self.workshops],
            "competitions": [item.to_dict() for item in self.competitions],
            "posters": [item.to_dict() for item in self.posters],
        }


class NIPSRetrieval:
    def __init__(self) -> None:
        pass

    def retrieval(
        self, html_content: str, text_filter: Callable[[str], bool]
    ) -> NIPSPageInfo:
        result = NIPSPageInfo()
        bs = BeautifulSoup(html_content, "html.parser")
        self._append_items(
            ".expo-talk-panel",
            result.talks,
            bs,
            text_filter,
        )
        self._append_items(
            ".expo-workshop",
            result.expo_workshops,
            bs,
            text_filter,
        )
        self._append_items(
            ".workshop",
            result.workshops,
            bs,
            text_filter,
        )
        self._append_items(
            ".competition",
            result.competitions,
            bs,
            text_filter,
        )
        self._append_items(
            ".content.poster",
            result.posters,
            bs,
            text_filter,
        )
        return result

    def _append_items(
        self,
        selector: str,
        store_container: List[NIPSItem],
        bs: BeautifulSoup,
        text_filter: Callable[[str], bool],
    ):
        panels = bs.select(selector)
        for panel in panels:
            a = panel.find("a")
            if text_filter(a.text):
                store_container.append(
                    NIPSItem("https://nips.cc" + a["href"], a.text.strip())
                )


class NIPSPosterItem:
    def __init__(self, author: str, abstract: str) -> None:
        self.author = author
        self.abstract = abstract

    def __str__(self) -> str:
        return f"author:[{self.author}]-abstract[{self.abstract}]"

    def to_dict(self) -> dict:
        return {"author": self.author, "abstract": self.abstract}


class NIPSPosterAbstractRetrieval:
    def __init__(self) -> None:
        pass

    def retrieval(self, html_content: str) -> NIPSPosterItem:
        bs = BeautifulSoup(html_content, "html.parser")
        abstract_example = bs.select_one("#abstractExample")
        if abstract_example.find("p") is None:
            abstract = abstract_example.text.strip()
        else:
            abstract = abstract_example.find("p").text.strip()
        if abstract.startswith("Abstract:"):
            abstract = abstract[9:]
        abstract = abstract.strip()
        author = bs.select_one(".card-subtitle").text.strip()
        return NIPSPosterItem(author, abstract)


class TranslatorEN2ZH:
    def __init__(self) -> None:
        self._client = Client()

    def translate(self, text: str) -> str:
        try:
            response = self._client.chat.completions.create(
                model=Model(
                    name="gpt-3.5-turbo",
                    base_provider="openai",
                    best_provider=RetryProvider([Liaobots]),
                ),
                messages=[
                    {
                        "role": "user",
                        "content": f'Please translate this text:[{text}] to Chinese, return json format like this: {{"content": "result"}}',
                    }
                ],
            )
            result = json.loads(response.choices[0].message.content)
            return result["content"]
        except Exception as e:
            raise Exception("Failed to translate, error: " + str(e)) from e


class NIPSPosterJsonGenerator:
    def __init__(
        self,
        main_page_json_save_path: str,
        poster_abstract_json_save_path: str,
        failed_poster_abstract_json_save_path: str,
        failed_translate_abstract_json_save_path: str,
    ) -> None:
        self._main_page_url = "https://nips.cc/virtual/2023/calendar"
        self._main_page_json_save_path = main_page_json_save_path
        self._poster_abstract_json_save_path = poster_abstract_json_save_path
        self._failed_poster_abstract_json_save_path = (
            failed_poster_abstract_json_save_path
        )
        self._failed_translate_abstract_json_save_path = (
            failed_translate_abstract_json_save_path
        )

    def generate_poster_file(self, filter: Callable[[str], bool]):
        response = requests.get(self._main_page_url)
        if response.status_code != 200:
            return

        page_info = NIPSRetrieval().retrieval(response.text, filter)
        self._save_main_page(page_info)

        poster_dict: Dict[str, dict] = {}
        failed_posters: Dict[str, dict] = {}
        for poster in page_info.posters:
            self._try_retrieval_poster_item(
                poster.url, poster.title, poster_dict, failed_posters
            )

        self._save_dict(poster_dict, self._poster_abstract_json_save_path)
        self._save_dict(failed_posters, self._failed_poster_abstract_json_save_path)

    def translate_poster_abstract(self, translator: TranslatorEN2ZH):
        with open(self._poster_abstract_json_save_path, "r", encoding="utf-8") as f:
            poster_dict = json.load(f)

        failed_translations: Dict[str, dict] = {}
        for title, poster_item in poster_dict.items():
            self._try_translate_poster_abstract(
                translator,
                poster_item["url"],
                title,
                poster_dict,
                failed_translations,
            )

        self._save_dict(poster_dict, self._poster_abstract_json_save_path)
        self._save_dict(
            failed_translations, self._failed_translate_abstract_json_save_path
        )

    def retranslate_from_failed(self, translator: TranslatorEN2ZH):
        with open(
            self._failed_translate_abstract_json_save_path, "r", encoding="utf-8"
        ) as f:
            failed_translations = json.load(f)
        poster_dict: Dict[str, dict] = {}
        refailed_translations: Dict[str, dict] = {}

        with open(self._poster_abstract_json_save_path, "r", encoding="utf-8") as f:
            poster_dict = json.load(f)

        for title, error_and_url in failed_translations.items():
            self._try_translate_poster_abstract(
                translator,
                error_and_url["url"],
                title,
                poster_dict,
                refailed_translations,
            )

        self._save_dict(poster_dict, self._poster_abstract_json_save_path)
        self._save_dict(
            refailed_translations, self._failed_translate_abstract_json_save_path
        )

    def regenerate_from_failed(self):
        with open(
            self._failed_poster_abstract_json_save_path, "r", encoding="utf-8"
        ) as f:
            failed_posters = json.load(f)
        poster_dict: Dict[str, dict] = {}
        refailed_posters: Dict[str, dict] = {}

        with open(self._poster_abstract_json_save_path, "r", encoding="utf-8") as f:
            poster_dict = json.load(f)

        for title, error_and_url in failed_posters.items():
            self._try_retrieval_poster_item(
                error_and_url["url"], title, poster_dict, refailed_posters
            )

        self._save_dict(poster_dict, self._poster_abstract_json_save_path)
        self._save_dict(refailed_posters, self._failed_poster_abstract_json_save_path)

    def _save_main_page(self, page_info):
        with open(self._main_page_json_save_path, "w", encoding="utf-8") as f:
            json.dump(
                page_info.to_dict(),
                f,
                ensure_ascii=False,
            )

    def _save_dict(self, target_dict: dict, path: str):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(target_dict, f, ensure_ascii=False)

    def _try_translate_poster_abstract(
        self,
        translator: TranslatorEN2ZH,
        url: str,
        title: str,
        poster_dict: Dict[str, dict],
        failed_translations: Dict[str, dict],
    ):
        print("start to translate poster abstract, title: " + title)
        try:
            poster_dict[title]["abstract_zh"] = translator.translate(
                poster_dict[title]["abstract"].replace("\\", "\\\\")
            )
            print("translate success, title: " + title)
        except Exception as e:
            failed_translations[title] = {
                "error": str(e),
                "url": url,
            }
            print("translate failed, title: " + title, "error: " + str(e))

    def _try_retrieval_poster_item(
        self,
        url: str,
        title: str,
        poster_dict: Dict[str, dict],
        failed_posters: Dict[str, dict],
    ):
        print("start to retrieve poster abstract, title: " + title + ", url: " + url)
        try:
            response = requests.get(url)
            if response.status_code != 200:
                raise Exception("Failed to retrieve poster page")
            poster_item = NIPSPosterAbstractRetrieval().retrieval(response.text)
            poster_dict[title] = {
                "author": poster_item.author,
                "abstract": poster_item.abstract,
                "url": url,
            }
        except Exception as e:
            failed_posters[title] = {
                "error": str(e),
                "url": url,
            }


class NIPSPosterJson2Md:
    def __init__(self, poster_abstract_json_path: str) -> None:
        self._poster_abstract_json_path = poster_abstract_json_path

    def generate_md(self, output_path: str):
        with open(self._poster_abstract_json_path, "r", encoding="utf-8") as f:
            poster_dict = json.load(f)
        with open(output_path, "w", encoding="utf-8") as f:
            for title, poster_item in poster_dict.items():
                f.write(f"## {title}\n")
                f.write(f"**Author**: {poster_item['author']}\n\n")
                f.write(f"**Abstract**: {poster_item['abstract']}\n\n")
                f.write(f"**Abstract(Chinese)**: {poster_item['abstract_zh']}\n\n")
                f.write(f"**URL**: {poster_item['url']}\n\n")
                f.write(f"---\n\n")
