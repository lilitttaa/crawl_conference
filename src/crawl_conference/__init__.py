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


class NIPSPageInfo:
    def __init__(self) -> None:
        self.talks: List[NIPSItem] = []
        self.expo_workshops: List[NIPSItem] = []
        self.workshops: List[NIPSItem] = []
        self.competitions: List[NIPSItem] = []
        self.posters: List[NIPSItem] = []


class NIPSRetrieval:
    def __init__(self) -> None:
        pass

    def retrieval(
        self, html_content: str, text_filter: Callable[[str], bool]
    ) -> NIPSPageInfo:
        result = NIPSPageInfo()
        bs = BeautifulSoup(html_content, "html.parser")
        expo_talk_panels = bs.select(".expo-talk-panel")
        for expo_talk_panel in expo_talk_panels:
            a = expo_talk_panel.find("a")
            if text_filter(a.text):
                result.talks.append(NIPSItem(a["href"], a.text.strip()))

        expo_workshop_panels = bs.select(".expo-workshop")
        for expo_workshop_panel in expo_workshop_panels:
            a = expo_workshop_panel.find("a")
            if text_filter(a.text):
                result.expo_workshops.append(NIPSItem(a["href"], a.text.strip()))

        workshop_panels = bs.select(".workshop")
        for workshop_panel in workshop_panels:
            a = workshop_panel.find("a")
            if text_filter(a.text):
                result.workshops.append(NIPSItem(a["href"], a.text.strip()))

        competition_panels = bs.select(".competition")
        for competition_panel in competition_panels:
            a = competition_panel.find("a")
            if text_filter(a.text):
                result.competitions.append(NIPSItem(a["href"], a.text.strip()))

        poster_panels = bs.select(".content.poster")
        for poster_panel in poster_panels:
            a = poster_panel.find("a")
            if text_filter(a.text):
                result.posters.append(NIPSItem(a["href"], a.text.strip()))
        return result


class NIPSPosterAbstractRetrieval:
    def __init__(self) -> None:
        pass

    def retrieval(self, html_content: str) -> str:
        bs = BeautifulSoup(html_content, "html.parser")
        abstract = bs.select_one("#abstractExample").find("p").text
        return abstract
