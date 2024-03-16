import json
import os
from typing import Callable, Dict
import requests
import sys

sys.path.append(r"./src/")
print(sys.path, os.getcwd())
from crawl_conference import (
    NIPSPosterJsonGenerator,
    TranslatorEN2ZH,
    reinforcement_learning_filter,
)


if __name__ == "__main__":
    generator = NIPSPosterJsonGenerator(
        "./result/nips_2023.json",
        "./result/nips_2023_poster_abstract.json",
        "./result/nips_2023_failed_poster_abstract.json",
        "./result/nips_2023_failed_translate_abstract.json",
    )
    # generator.generate_poster_file(reinforcement_learning_filter)
    # generator.regenerate_from_failed()
    # generator.translate_poster_abstract(TranslatorEN2ZH())
    generator.retranslate_from_failed(TranslatorEN2ZH())
