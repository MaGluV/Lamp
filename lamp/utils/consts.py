import os
import re

ENV_FILE = os.path.join('..', '.env')

params = dict(re.findall('([a-zA-Z_]+)=(.*)', open(ENV_FILE, 'r').read()))

ROOT_PATH = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
LOGGER_CONFIG = os.path.join(ROOT_PATH, '.loggingconfig.yaml')

DEFAULT_DEVICE_NAME = 'cpu'
DEFAULT_MODEL = 'mistralai/Mistral-7B-Instruct-v0.3'
DEFAULT_ACCESS_TOKEN = params['DEFAULT_ACCESS_TOKEN']
DEFAULT_GENERATOR_PARAMS = {
    'max_new_tokens': 4096,
    'do_sample': True,
    'temperature': 0.9,
    'top_k': 50,
    'top_p': 0.95,
    # "eos_token_id": tokenizer.eos_token_id,
    # "pad_token_id": tokenizer.pad_token_id,
    # "repetition_penalty": 1.5,
    # "no_repeat_ngram_size": 5,
}

DEFAULT_STRIP_LIST = ['</s>']
ENV_FILE = os.path.join('..', '.env')
