import logging
import os
from datetime import date
from typing import Union

from celery import Celery
from celery.signals import after_setup_logger
from sqlmodel import Field, SQLModel, create_engine
from utils.logger import get_logger

CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND')
USER = os.getenv('POSTGRES_USER')
PASSWORD = os.getenv('POSTGRES_PASSWORD')
PORT = os.getenv('POSTGRES_PORT')
HOST = os.getenv('POSTGRES_HOST')
DB = os.getenv('POSTGRES_DB')


celery_app = Celery(
    'celery',
    backend=CELERY_BROKER_URL,
    broker=CELERY_RESULT_BACKEND,
)

for f in ['./broker/out', './broker/processed']:
    if not os.path.exists(f):
        os.makedirs(f)


logger = get_logger(__name__)


@after_setup_logger.connect
def setup_loggers(logger, *args, **kwargs):
    fh = logging.FileHandler('logs.log')
    logger.addHandler(fh)


engine = create_engine(
    f'postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB}'
)


class Lamp_Users(SQLModel, table=True):
    user_id: Union[int, None] = Field(default=None, primary_key=True)
    user_name: str = Field(default='max', index=True)
    user_password: str = Field(default='qwerty', index=True)
    registration_date: date = Field(default=date.today())


class Lamp_Projects(SQLModel, table=True):
    project_id: Union[int, None] = Field(default=None, primary_key=True)
    project_name: str = Field(default='project_1', index=True)
    user_id: Union[int, None] = Field(default=None, foreign_key='lamp_users.user_id')


class Lamp_Prompts(SQLModel, table=True):
    prompt_id: Union[int, None] = Field(default=None, primary_key=True)
    prompt: str = Field(default='How to make a cheesecake?')
    project_id: Union[int, None] = Field(default=None, foreign_key='lamp_projects.project_id')


class Lamp_Results(SQLModel, table=True):
    code_id: Union[int, None] = Field(default=None, primary_key=True)
    result_func: str = Field(default='def a(): pass')
    result_date: date = Field(default=date.today())
    project_id: Union[int, None] = Field(default=None, foreign_key='lamp_projects.project_id')
    prompt_id: Union[int, None] = Field(default=None, foreign_key='lamp_prompts.prompt_id')
