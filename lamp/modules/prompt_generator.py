from typing import Dict, List

import requests

from .base_generator import BaseGenerator


class PromptGenerator(BaseGenerator):
    def __init__(self, config: Dict):
        self.partitions = config.get('partitions', 10)

    def _specify_libraries(self, libs: List) -> str:
        if len(libs) > 1:
            libs = ', '.join(libs)
            return f'Use only {libs} libraries for extracting image link. '
        if not libs:
            return ''
        return f'Use only {libs[0]} library for extracting image link. '

    def _specify_tag(self, data_type: str, tag: str, attribute: str) -> str:
        if not tag or not attribute:
            return ''
        return f'The {data_type} must be in {attribute} attribute of {tag} HTML tag. '

    def _specify_not_found_confition(self, data_type: str, not_found_condition: str) -> str:
        if not not_found_condition:
            return ''
        return f'If no {data_type} was found, the function must return {not_found_condition}. '

    def _specify_special_codition(self, data_type: str, spec_condition: str) -> str:
        if not spec_condition:
            return ''
        return f'The {data_type} should {spec_condition}. '

    def _specify_return_format(self, data_type: str, ret_format: str) -> str:
        if not ret_format:
            return ''
        return f'The function must return a {ret_format} with the expected {data_type}. '

    def _specify_expected_result(self, data_type: str, expected_result: str) -> str:
        if not expected_result:
            return ValueError(f'Invalid expected result - {expected_result}')
        return f'The {data_type} that function shoud return is {expected_result}. '

    def _specify_text_split(self, data_type: str, parts_num: int = None):
        nums = ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten']
        if not parts_num or parts_num < 0 or parts_num >= len(nums):
            return ''
        prompt = (
            f'The function must split html code in {nums[parts_num - 1]} equal '
            f'parts and search the {data_type} in each part. ')
        return prompt

    def generate_prompt(
        self,
        data_type: str,
        libs: List,
        tag: str,
        attribute: str,
        not_found_condition: str,
        spec_condition: str,
        ret_format: str,
        url: str,
        expected_result: str,
        parts_num: int = None,
        idx: int = None,
    ):
        query = 'You are a code generating bot.'
        task = (
            'to create a Python function for extracting certain '
            f'{data_type} from html code, putted in <<<>>>.'
        )
        requirements = ''.join(
            (
                self._specify_libraries(libs),
                self._specify_text_split(data_type, parts_num),
                self._specify_not_found_confition(data_type, not_found_condition),
                self._specify_special_codition(data_type, spec_condition),
                self._specify_tag(data_type, tag, attribute),
                self._specify_expected_result(data_type, expected_result),
                self._specify_return_format(data_type, ret_format)
            )
        )
        page = requests.get(url)
        html_text = page.text
        if idx > 0 and idx <= self.partitions:
            start = (idx - 1) * len(html_text) // self.partitions
            stop = idx * len(html_text) // self.partitions - 1
            html_text = html_text[start: stop]
        prompt = (
            f'{query} Your task is {task} {requirements}\n\n'
            f'\n\n<<<{html_text}'
            '>>>'
        )
        return [prompt]
