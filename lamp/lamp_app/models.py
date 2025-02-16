from datetime import date
# from sqlalchemy import DateTime
from typing import Union

from sqlmodel import Field, SQLModel


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


class Tokens(SQLModel, table=True):
    user_id: Union[int, None] = Field(default=None, foreign_key='lamp_users.user_id')
    access_token: str = Field(default='qwerty', primary_key=True)
    refresh_token: Union[str, None] = Field(default='qwerty', index=True)
    status: bool = Field(default=False)
    creation_date: date = Field(default=date.today())
