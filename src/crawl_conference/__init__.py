from typing import Callable, List

from bs4 import BeautifulSoup


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


class NIPSPosterAbstractRetrieval:
    def __init__(self) -> None:
        pass

    def retrieval(self, html_content: str) -> str:
        bs = BeautifulSoup(html_content, "html.parser")
        abstract = bs.select_one("#abstractExample").find("p").text
        return abstract
