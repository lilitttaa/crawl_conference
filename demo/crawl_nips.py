import json
import os
from typing import Dict
import requests
import sys

sys.path.append(r"./src/")
print(sys.path, os.getcwd())
from crawl_conference import (
    NIPSPosterAbstractRetrieval,
    NIPSRetrieval,
    reinforcement_learning_filter,
)


def generate_poster_json_file():
    response = requests.get("https://nips.cc/virtual/2023/calendar")
    if response.status_code != 200:
        return
    page_info = NIPSRetrieval().retrieval(response.text, reinforcement_learning_filter)

    with open("./result/nips_2023.json", "w", encoding="utf-8") as f:
        json.dump(
            page_info.to_dict(),
            f,
            ensure_ascii=False,
        )

    poster_dict: Dict[str, str] = {}
    failed_posters: Dict[str, str] = {}
    for poster in page_info.posters:
        print(
            "start to retrieve poster abstract, title: ",
            poster.title,
            ", url: ",
            poster.url,
        )
        try:
            response = requests.get(poster.url)
            if response.status_code != 200:
                raise Exception("Failed to retrieve poster page")
            poster_item = NIPSPosterAbstractRetrieval().retrieval(response.text)
            poster_dict[poster.title] = poster_item.to_dict()
        except Exception as e:
            failed_posters[poster.title] = {
                "error": str(e),
                "url": poster.url,
            }

    with open("./result/nips_2023_poster_abstract.json", "w", encoding="utf-8") as f:
        json.dump(poster_dict, f, ensure_ascii=False)

    with open(
        "./result/nips_2023_failed_poster_abstract.json", "w", encoding="utf-8"
    ) as f:
        json.dump(failed_posters, f, ensure_ascii=False)


def handle_failed_posters():
    with open(
        "./result/nips_2023_failed_poster_abstract.json", "r", encoding="utf-8"
    ) as f:
        failed_posters = json.load(f)
    poster_dict: Dict[str, str] = {}
    refailed_posters: Dict[str, str] = {}

    with open("./result/nips_2023_poster_abstract.json", "r", encoding="utf-8") as f:
        poster_dict = json.load(f)

    for title, error_and_url in failed_posters.items():
        url = error_and_url["url"]
        error = error_and_url["error"]
        print(
            "start to retrieve poster abstract, title: ",
            title,
            ", url: ",
            url,
        )
        try:
            response = requests.get(url)
            if response.status_code != 200:
                raise Exception("Failed to retrieve poster page")
            poster_item = NIPSPosterAbstractRetrieval().retrieval(response.text)
            poster_dict[title] = poster_item.to_dict()
        except Exception as e:
            print("Failed to retrieve poster abstract, title: ", title, ", url: ", url)
            print(e)
            refailed_posters = {
                "error": str(e),
                "url": url,
            }
    with open("./result/nips_2023_poster_abstract.json", "w", encoding="utf-8") as f:
        json.dump(poster_dict, f, ensure_ascii=False)

    with open(
        "./result/nips_2023_failed_poster_abstract.json", "w", encoding="utf-8"
    ) as f:
        json.dump(refailed_posters, f, ensure_ascii=False)


def request_poster():
    response = requests.get("https://nips.cc/virtual/2023/poster/71095")
    if response.status_code == 200:
        with open(
            os.path.join(os.path.abspath(os.getcwd()), "tests/assets/poster2.html"), "w"
        ) as f:
            f.write(response.text)


def strip_author():
    with open("./result/nips_2023_poster_abstract.json", "r", encoding="utf-8") as f:
        poster_dict = json.load(f)
    new_poster_dict = {}
    for title, poster in poster_dict.items():
        author: str = poster["author"]
        new_poster_dict[title] = {
            "author": author.strip(),
            "abstract": poster["abstract"],
        }

    with open("./result/nips_2023_poster_abstract.json", "w", encoding="utf-8") as f:
        json.dump(new_poster_dict, f, ensure_ascii=False)


if __name__ == "__main__":
    strip_author()
