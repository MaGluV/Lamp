import json
import re
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import List

import lamp_app.schemas as schemas
import requests
from bs4 import BeautifulSoup
from fastapi import BackgroundTasks, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import ORJSONResponse
from lamp_app.cors import app
from lamp_app.models import (Lamp_Projects, Lamp_Prompts, Lamp_Results,
                             Lamp_Users, Tokens)
from lamp_app.tokens import (JWTBearer, create_access_token,
                             create_refresh_token, decode_jwt,
                             get_hashed_password, token_required,
                             verify_password)
from lamp_app.utils import SessionDep, create_db_and_tables
from lamp_app.worker import celery_app
from modules.prompt_generator import PromptGenerator
from sqlmodel import select
from utils.logger import get_logger


@app.post('/register/')
async def create_user(user: Lamp_Users, session: SessionDep) -> Lamp_Users:
    query = select(Lamp_Users).filter_by(user_name=user.user_name)
    query_all_users = select(Lamp_Users)
    existing_users = session.exec(query)
    existing_user = existing_users.first()
    if existing_user:
        raise HTTPException(status_code=400, detail='Username already registered')

    encrypted_password = get_hashed_password(user.user_password)
    new_user = Lamp_Users(
        user_id=len(session.exec(query_all_users).all()),
        user_name=user.user_name,
        user_password=encrypted_password
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user


@app.post('/login', response_model=schemas.TokenSchema)
async def login(request: schemas.RequestDetails, session: SessionDep) -> Tokens:
    query = select(Lamp_Users).filter(Lamp_Users.user_name == request.user_name)
    users = session.exec(query)
    user = users.first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='Incorrect username'
        )
    hashed_pass = user.user_password
    if not verify_password(request.user_password, hashed_pass):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Incorrect password'
        )

    access = create_access_token(user.user_id)
    refresh = create_refresh_token(user.user_id)

    token_db = Tokens(
        user_id=user.user_id,
        access_token=access,
        refresh_token=refresh,
        status=True
    )
    session.add(token_db)
    session.commit()
    session.refresh(token_db)
    return token_db


@app.get('/getusers')
@token_required
async def get_users(session: SessionDep, dependencies=Depends(JWTBearer())) -> List[Lamp_Users]:
    query = select(Lamp_Users)
    users = session.exec(query)
    return jsonable_encoder(users.all())


@app.post('/change-password', response_class=ORJSONResponse)
async def change_pass(request: schemas.ChangePassword, session: SessionDep) -> ORJSONResponse:
    query = select(Lamp_Users).filter(Lamp_Users.user_name == request.user_name)
    users = session.exec(query)
    user = users.first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User not found')

    if not verify_password(request.old_password, user.user_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid old password')

    encrypted_password = get_hashed_password(request.new_password)
    user.user_password = encrypted_password
    session.commit()

    return ORJSONResponse([{'message': 'Password changed successfully'}])


@token_required
@app.post('/logout', response_class=ORJSONResponse)
async def logout_user(session: SessionDep, dependencies=Depends(JWTBearer())) -> ORJSONResponse:
    token = dependencies
    payload = decode_jwt(token)
    user_id = payload['sub']
    query = select(Tokens)
    token_records = session.exec(query)
    token_record = token_records.all()
    info = []
    for record in token_record:
        if (datetime.now(timezone.utc).date() - record.creation_date).days > 1:
            info.append(record.user_id)
    if info:
        query = select(Tokens).where(Tokens.user_id.in_(info))
        existing_token = session.exec(query)
        session.delete(existing_token.first())
        session.commit()

    query = select(Tokens).filter(
        Tokens.user_id == user_id,
        Tokens.access_token == token
    )
    existing_tokens = session.exec(query)
    existing_token = existing_tokens.first()
    if existing_token:
        existing_token.status = False
        session.add(existing_token)
        session.commit()
        session.refresh(existing_token)
    return ORJSONResponse([{'message': 'Logout Successfully'}])


@token_required
@app.post('/new-project')
async def create_new_project(
    project: Lamp_Projects,
    session: SessionDep,
    dependencies=Depends(JWTBearer())
) -> Lamp_Projects:
    query = select(Lamp_Projects).filter_by(project_name=project.project_name)
    existing_projects = session.exec(query)
    existing_project = existing_projects.first()
    if existing_project:
        raise HTTPException(
            status_code=400,
            detail=f'Project {project.project_name} already registered'
        )
    tokens_query = select(Tokens).filter_by(access_token=dependencies)
    token = session.exec(tokens_query).first()
    query_all_projects = select(Lamp_Projects)
    new_project = Lamp_Projects(
        project_id=len(session.exec(query_all_projects).all()),
        project_name=project.project_name,
        user_id=token.user_id
    )
    session.add(new_project)
    session.commit()
    session.refresh(new_project)
    return new_project


@token_required
@app.get('/get-projects')
async def get_projects(
    session: SessionDep,
    dependencies=Depends(JWTBearer())
) -> List[Lamp_Projects]:
    tokens_query = select(Tokens).filter_by(access_token=dependencies)
    token = session.exec(tokens_query).first()
    query = select(Lamp_Projects).filter_by(user_id=token.user_id)
    projects = session.exec(query)
    return jsonable_encoder(projects.all())


@token_required
@app.post('/generate-prompt/{project_id}')
async def generate_prompt(
    project_id: int,
    request: schemas.PromptSchema,
    session: SessionDep,
    dependencies=Depends(JWTBearer())
) -> Lamp_Prompts:
    config = {'logger': get_logger(PromptGenerator.__name__)}
    pg = PromptGenerator(config)
    result = pg.generate_prompt(
        request.data_type,
        request.libs,
        request.tag,
        request.attribute,
        request.not_found_condition,
        request.spec_condition,
        request.ret_format,
        request.url,
        request.expected_result,
        request.parts_num,
        request.idx
    )

    query_all_prompts = select(Lamp_Prompts)
    new_prompt = Lamp_Prompts(
        prompt_id=len(session.exec(query_all_prompts).all()),
        prompt=json.dumps(result),
        project_id=project_id
    )
    session.add(new_prompt)
    session.commit()
    session.refresh(new_prompt)
    return new_prompt


@token_required
@app.get(
    '/get-last-prompt/{project_id}',
    response_class=ORJSONResponse
)
async def get_last_prompt(
    project_id: int,
    session: SessionDep,
    dependencies=Depends(JWTBearer())
) -> Lamp_Prompts:
    query = select(Lamp_Prompts).filter_by(project_id=project_id)
    projects = session.exec(query).all()
    if not projects:
        return ORJSONResponse([{'message': f'Project {project_id} is empty'}])
    max_pid = max([project.prompt_id for project in projects])
    query = select(Lamp_Prompts).filter_by(prompt_id=max_pid)
    prompts = session.exec(query)
    return prompts.first()


@token_required
@app.get(
    '/get-prompt/{prompt_id}',
    response_class=ORJSONResponse
)
async def get_prompt(
    prompt_id: int,
    session: SessionDep,
    dependencies=Depends(JWTBearer())
) -> Lamp_Prompts:
    query = select(Lamp_Prompts)
    projects = session.exec(query).all()
    prompts = [project.prompt_id for project in projects]
    if prompt_id not in prompts:
        return ORJSONResponse([{'message': f"Prompt {prompt_id} doesn't exist"}])
    query = select(Lamp_Prompts).filter_by(prompt_id=prompt_id)
    filters = session.exec(query)
    return filters.first()


@token_required
@app.post(
    '/start_generator/{project_id}/{prompt_id}',
    response_class=ORJSONResponse
)
async def start_generator(
    project_id: int,
    prompt_id: int,
    request: schemas.CodeGeneratorSchema,
    session: SessionDep,
    dependencies=Depends(JWTBearer())
) -> ORJSONResponse:
    query = select(Lamp_Prompts).filter_by(prompt_id=prompt_id)
    prompt = session.exec(query).first()
    config = {}
    query_results = select(Lamp_Results)
    code_id = len(session.exec(query_results).all())
    task = celery_app.send_task(
        'generator.task',
        args=[
            code_id,
            project_id,
            prompt_id,
            config,
            json.loads(prompt.prompt),
            request.test_url,
            request.test_result
        ]
    )
    return dict(
        task_id=task.id,
        url=f"/check_task/{task.id}",
    )


@app.get('/drop_task/{task_id}')
def drop_task(task_id: str):
    celery_app.control.revoke(task_id, terminate=True)


@app.get('/check_task/{task_id}')
def check_task(task_id: str):
    task = celery_app.AsyncResult(task_id)

    if task.state == 'SUCCESS':
        response = {
            'status': task.state,
            'result': task.result,
            'task_id': task_id,
        }

    elif task.state == 'FAILURE':
        response = json.loads(
            task.backend.get(
                task.backend.get_key_for_task(task.id),
            ).decode('utf-8')
        )
        del response['children']
        del response['traceback']

    else:
        response = {
            'status': task.state,
            'result': task.info,
            'task_id': task_id,
        }

    return response


@token_required
@app.get(
    '/get-last-generated-code/{project_id}',
    response_class=ORJSONResponse
)
async def generated_code(
    project_id: int,
    session: SessionDep,
    dependencies=Depends(JWTBearer())
) -> Lamp_Results:
    query = select(Lamp_Results).filter_by(project_id=project_id)
    projects = session.exec(query).all()
    if not projects:
        return ORJSONResponse([{'message': f'Project {project_id} is empty'}])
    max_pid = max([project.code_id for project in projects])
    query = select(Lamp_Results).filter_by(code_id=max_pid)
    code = session.exec(query).first()
    return code


@token_required
@app.post('/execute-code/{code_id}')
async def execute_code(
    code_id: int,
    request: schemas.ExecParams,
    session: SessionDep,
    dependencies=Depends(JWTBearer())
) -> schemas.CodeResultsSchema:
    query = select(Lamp_Results).filter_by(code_id=code_id)
    code = session.exec(query).first()
    url = request.url
    replacing_line = f'requests.get("{url}")'
    exec_code = re.sub(r'requests.get\(\S+', replacing_line, code.result_func)
    exec(exec_code)
    results_file = open('test_results.json', 'r').read()
    code_results = schemas.CodeResultsSchema(results=results_file)
    return code_results
