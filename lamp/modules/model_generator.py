import json
import re
from typing import Any, Dict, List

import requests  # noqa: F401
import torch
from bs4 import BeautifulSoup  # noqa: F401
from transformers import AutoModelForCausalLM, AutoTokenizer
from utils.consts import (DEFAULT_ACCESS_TOKEN, DEFAULT_DEVICE_NAME,
                          DEFAULT_GENERATOR_PARAMS, DEFAULT_MODEL,
                          DEFAULT_STRIP_LIST)

from .base_generator import BaseGenerator


class ModelGenerator(BaseGenerator):
    def __init__(self, config: Dict):
        super().__init__(config)
        self._model_name = self._config.get('model_name', DEFAULT_MODEL)
        self._device_name = self._config.get('device_name', DEFAULT_DEVICE_NAME)
        self._params = self._config.get('generator_params', DEFAULT_GENERATOR_PARAMS)
        self._token = self._config.get('access_token', DEFAULT_ACCESS_TOKEN)

        self._model = AutoModelForCausalLM.from_pretrained(
            self._model_name, device_map=self._device_name, use_auth_token=self._token
        )
        self._tokenizer = AutoTokenizer.from_pretrained(
            self._model_name, use_auth_token=self._token
        )
        self._device = torch.device(self._device_name)
        self._model.to(self._device)

    def python_code_generator(
        self,
        prompt: list,
        test_url: str,
        test_result: str,
    ):
        if not isinstance(prompt, list) and not isinstance(prompt[0], str):
            raise ValueError(f'Invalid prompt - {prompt}')
        python_code = None
        attempt = 1
        while True:
            self._logger.info(f'Attempt {attempt}')
            attempt += 1
            self._logger.info('Start generator')
            model_response = self._model_generate(prompt)
            self._logger.info('Extract function')
            try:
                python_func, function_name = self._get_python_function(model_response)
            except IndexError as err:
                self._logger.info(err)
                continue
            self._logger.info('Assemble executable code')
            if function_name and python_func:
                python_code = self._get_full_executable_code(
                    python_func, function_name, test_url
                )
                self._logger.info(
                    f'Generated function is {function_name} - {python_code}'
                )
                extract_code = self._get_exec()
                python_code = ''.join((python_code, extract_code))
            else:
                err = 'No function name or function itself was extracted'
                self._logger.info(err)
                continue
            self._logger.info('Execute code')
            try:
                exec(python_code)
            except SyntaxError as err:
                self._logger.info(err)
                continue
            # TODO: read result from temporary directory
            results_file = open('test_results.json', 'r')
            results = json.load(results_file)
            self._logger.info(results)
            if test_result in results[0]:
                break
        return python_code

    def _get_python_function(
        self, model_response: str, strip_list: List[str] = DEFAULT_STRIP_LIST
    ):
        python_func = None
        function_name = None
        result = model_response[0]
        result = f'{result}\n'
        python_func = re.findall(r'.+(def .+return \S+)\n', result, flags=re.S)[0]
        function_name = re.findall(r'def (\S*)\(.*\)', python_func)[0]
        for tag in strip_list:
            python_func = python_func.replace(tag, '')
        return python_func, function_name

    def _get_full_executable_code(
        self, python_func: str, function_name: str, test_url: str
    ) -> str:
        additional_code = (
            '\n'
            '\n'
            f'request = requests.get("{test_url}")\n'
            'html = request.text\n'
            'try:\n'
            f'    results = {function_name}(html)\n'
            'except Exception as e:\n'
            '    print(e)\n'
            '    results = [""]\n'
            'results = results if results else [""]'
        )
        return f'\n{python_func}\n{additional_code}'

    def _get_exec(self):
        # TODO: save result in temporary directory
        extract_code = (
            '\n'
            'with open("test_results.json", "w") as wt:\n'
            '   json.dump(results, wt)'
        )
        return extract_code

    def _model_generate(self, prompt: list, apply_temp: bool = False) -> Any:
        if apply_temp:
            try:
                model_inputs = self._tokenizer.apply_chat_template(
                    prompt, return_tensors='pt'
                ).to(self._device_name)
            except Exception as e:
                raise ValueError(f'Tokenizer stopped with error - {e}')
        else:
            try:
                model_inputs = self._tokenizer(prompt, return_tensors='pt').to(
                    self._device_name
                )
            except Exception as e:
                raise ValueError(f'Tokenizer stopped with error - {e}')
        try:
            generated_ids = self._model.generate(**model_inputs, **self._params)
        except Exception as e:
            raise ValueError(f'Generation stopped with error - {e}')
        try:
            results = self._tokenizer.batch_decode(generated_ids)
        except Exception as e:
            raise ValueError(f'Decoding stopped with error - {e}')
        return results
