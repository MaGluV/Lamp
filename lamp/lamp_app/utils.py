import os
import re
from typing import Annotated

from fastapi import Depends
from lamp_app.models import Lamp_Results
from modules.model_generator import ModelGenerator
from sqlmodel import Session, SQLModel, create_engine

ENV_FILE = os.path.join('..', '.env')
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 1 day
REFRESH_TOKEN_EXPIRE_MINUTES = 10080  # 7 days
ALGORITHM = 'HS256'
JWT_SECRET_KEY = re.findall(r'SECRET_KEY=(\S+)', open(ENV_FILE, 'r').read())[0]
JWT_REFRESH_SECRET_KEY = re.findall(r'REFRESH_KEY=(\S+)', open(ENV_FILE, 'r').read())[0]


def get_postgre_url() -> str:
    params = dict(re.findall('([a-zA-Z_]+)=(.*)', open(ENV_FILE, 'r').read()))

    user = params['POSTGRES_USER']
    password = params['POSTGRES_PASSWORD']
    port = params['DEV_PORT'].strip('"').split(':')[0]
    host = ':'.join((params['POSTGRES_HOST'], port))
    db = params['POSTGRES_DB']

    return f'postgresql+psycopg2://{user}:{password}@{host}/{db}'


engine = create_engine(get_postgre_url())


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def run_model(
    config: dict,
    project_id: int,
    prompt_id: int,
    code_id: int,
    prompt: str,
    test_url: str,
    test_result: str,
    session: SessionDep,
):
    new_code = Lamp_Results(
        code_id=code_id,
        result_func='',
        project_id=project_id,
        prompt_id=prompt_id
    )
    session.add(new_code)
    session.commit()
    session.refresh(new_code)
    model = ModelGenerator(config)
    code = model.python_code_generator(
        prompt, test_url, test_result
    )
    new_code.result_func = code
    session.add(new_code)
    session.commit()
    session.refresh(new_code)
