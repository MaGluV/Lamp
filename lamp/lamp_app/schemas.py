import datetime
from typing import List, Union

from pydantic import BaseModel, Field


class UsersSchema(BaseModel):
    user_id: int
    user_name: str
    user_password: str
    registration_date: datetime.datetime


class PromptSchema(BaseModel):
    data_type: str
    libs: List
    tag: str
    attribute: str
    not_found_condition: str
    spec_condition: str
    ret_format: str
    url: str
    expected_result: str
    parts_num: Union[int, None] = Field(default=None, frozen=True)
    idx: int = Field(default=None, frozen=True)


class CodeGeneratorSchema(BaseModel):
    test_url: str
    test_result: str


class CodeResultsSchema(BaseModel):
    results: str


class RequestDetails(BaseModel):
    user_name: str
    user_password: str


class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str


class ChangePassword(BaseModel):
    user_name: str
    old_password: str
    new_password: str


class TokenCreate(BaseModel):
    user_id: int
    access_token: str
    refresh_token: str
    status: bool
    creation_date: datetime.datetime
