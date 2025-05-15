import traceback

from celery import states
from modules.model_generator import ModelGenerator
from sqlmodel import Session
from worker import Lamp_Results, celery_app, engine, logger


@celery_app.task(name='generator.task', bind=True)
def run_model(
    self,
    code_id: int,
    project_id: int,
    prompt_id: int,
    config: dict,
    prompt: str,
    test_url: str,
    test_result: str
):
    config['logger'] = logger
    logger.info('ModelGenerator start')
    model = ModelGenerator(config)
    self.update_state(state='PROGRESS')
    try:
        code = model.python_code_generator(
            prompt, test_url, test_result
        )
    except Exception as ex:
        self.update_state(
            state=states.FAILURE,
            meta={
                'exc_type': type(ex).__name__,
                'exc_message': traceback.format_exc().split('\n'),
            },
        )
    with Session(engine) as session:
        new_code = Lamp_Results(
            code_id=code_id,
            result_func=code,
            project_id=project_id,
            prompt_id=prompt_id
        )
        session.add(new_code)
        session.commit()
        session.refresh(new_code)
    return code
