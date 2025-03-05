from logging import Logger
from re import Pattern
import re
from typing import Dict, List, Optional, Tuple, Union

from phonemizer.backend.espeak.espeak import EspeakBackend
from phonemizer.backend.espeak.language_switch import LanguageSwitch
from phonemizer.backend.espeak.words_mismatch import WordMismatch


class CustomEspeakBackend(EspeakBackend):
    def __init__(self, language: str,
                 punct_regex: Optional[str] = '',
                 preserve_regex: Optional[List[str]] = [],
                 with_stress: bool = True,
                 tie: Union[bool, str] = False,
                 language_switch: LanguageSwitch = 'keep-flags',
                 words_mismatch: WordMismatch = 'ignore',
                 logger: Optional[Logger] = None):
        self.token = "<|begin_real_number|> {content}"
        self.regex = '|'.join([f'({pattern})' for pattern in preserve_regex])

        super().__init__(
            language,
            punctuation_marks=re.compile(punct_regex),
            preserve_punctuation=True,
            with_stress=with_stress,
            tie=tie,
            language_switch=language_switch,
            words_mismatch=words_mismatch,
            logger=logger
        )

    def phonemize(self, text: List[str]) -> List[str]:
        if not self.regex:
            return super().phonemize(text)

        pre_process = [self.pre_process(
            txt, super().phonemize) for txt in text]
        phonemized = super().phonemize([txt for txt, _ in pre_process])
        post_txt = [self.post_process(phoneme, process[1])
                    for process, phoneme in zip(pre_process, phonemized)]

        return post_txt

    def pre_process(self, txt: str, phonemize):
        replacements = {}

        def replace_match(match):
            txt = match.group(0)
            content = self.token.format(content=txt)
            phoneme = phonemize([content])[0]
            replacements[phoneme.strip()] = txt

            return content

        processed_text = re.sub(self.regex, replace_match, txt)

        return processed_text, replacements

    def post_process(self, phoneme: str, replacements: Dict[str, str]):
        for replaced, replacement in replacements.items():
            if replaced in phoneme:
                phoneme = phoneme.replace(replaced, replacement)
            else:
                raise ValueError(
                    f"Replacement '{replaced}' not found in '{phoneme}'")

        return phoneme
