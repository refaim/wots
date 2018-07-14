import re
import string
from typing import Optional

from core.language import LOWERCASE_LETTERS_ENGLISH, LOWERCASE_LETTERS_RUSSIAN
from core.utils import load_json_resource, ILogger


class SetOracle(object):  # TODO single language sets
    def __init__(self, logger: ILogger, thorough: bool):
        self.__thorough = thorough
        self.__logger = logger
        self.__name_characters = LOWERCASE_LETTERS_ENGLISH | LOWERCASE_LETTERS_RUSSIAN | set(string.digits)
        self.__abbrvs_by_name_key = {}
        self.__names_by_abbrv = {}
        self.__patterns_by_abbrv = {}
        for abbreviation, (name, pattern) in load_json_resource('set_names.json').items():
            if pattern is None:
                pattern = name
            self.__abbrvs_by_name_key[self.__get_name_key(name)] = abbreviation
            self.__names_by_abbrv[abbreviation] = name
            self.__patterns_by_abbrv[abbreviation] = re.compile(r'^({})$'.format(pattern), re.IGNORECASE | re.UNICODE)

    def __get_name_key(self, value):
        return ''.join(c for c in value.lower() if c in self.__name_characters)

    def get_name(self, abbreviation: str) -> str:
        return self.__names_by_abbrv[abbreviation]

    def get_abbreviation(self, candidate: str, quiet: bool = False) -> Optional[str]:
        cleaned_candidate = candidate.strip().upper()
        if cleaned_candidate in self.__names_by_abbrv:
            return cleaned_candidate

        candidate_key = self.__get_name_key(cleaned_candidate)
        if candidate_key in self.__abbrvs_by_name_key:
            return self.__abbrvs_by_name_key[candidate_key]

        matches = []
        for abbreviation, regexp in self.__patterns_by_abbrv.items():
            if regexp.match(cleaned_candidate):
                if not self.__thorough:
                    return abbreviation
                matches.append(abbreviation)
        if self.__thorough and len(matches) > 0:
            if len(matches) > 1:
                raise Exception('Found {} for "{}"'.format(', '.join(matches), candidate))
            return matches[0]
        if not quiet:
            self.__logger.warning('Unable to recognize set "%s"', candidate)
        return None
