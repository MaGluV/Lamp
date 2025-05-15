include .env

# OLLAMA_PULL_AND_START:
# 	docker-compose -f docker-compose-ollama.yaml pull && docker-compose -f docker-compose-ollama.yaml up -d

# OLLAMA_START:
# 	docker-compose -f docker-compose-ollama.yaml up -d

# OLLAMA_MISTRAL_LOAD:
# 	docker exec -it ${OLLAMA_CONTAINER_ID} ollama run ${OLLAMA_MODEL}

# OLLAMA_STOP:
# 	docker-compose -f docker-compose-ollama.yaml stop

# vLLM_BUILD:
# 	cd vllm && DOCKER_BUILDKIT=1 docker build -f Dockerfile.cpu . -t vllm-cpu-env --build-arg max_jobs=8 --build-arg nvcc_threads=1

# vLLM_RUN:
# 	docker run -v ${vLLM_CACHE} --env ${vLLM_TOKEN} --env ${vLLM_CACHE_SIZE} --env ${vLLM_TIMEOUT} -p 8000:8000 --ipc=host vllm-cpu-env --model ${vLLM_MODEL} --tokenizer_mode mistral --load_format mistral --config_format mistral --max-model-len=128000

# vLLM_START:
# 	docker start ${vLLM_CONTAINER_NAME}

# vLLM_STOP:
# 	docker stop ${vLLM_CONTAINER_NAME}

.PHONY: CELERYBACKEND_PULL_AND_START
CELERYBACKEND_PULL_AND_START:
	docker-compose pull celerybackend && docker-compose up -d celerybackend

.PHONY: CELERYBACKEND_START
CELERYBACKEND_START:
	docker-compose start celerybackend

.PHONY: CELERYBACKEND_STOP
CELERYBACKEND_STOP:
	docker-compose stop celerybackend

.PHONY: FLOWER_PULL_AND_START
FLOWER_PULL_AND_START:
	docker-compose pull flower && docker-compose up -d flower

.PHONY: FLOWER_START
FLOWER_START:
	docker-compose start flower

.PHONY: FLOWER_STOP
FLOWER_STOP:
	docker-compose stop flower

.PHONY: WORKER_PULL_AND_START
WORKER_PULL_AND_START:
	docker-compose pull worker && docker-compose up --build -d worker

.PHONY: WORKER_START
WORKER_START:
	docker-compose start worker

.PHONY: WORKER_STOP
WORKER_STOP:
	docker-compose stop worker

.PHONY: POSTGRE_PULL_AND_START
POSTGRE_PULL_AND_START:
	docker-compose pull db && docker-compose up -d db

.PHONY: POSTGRE_START
POSTGRE_START:
	docker-compose start db

.PHONY: POSTGRE_STOP
POSTGRE_STOP:
	docker-compose stop db

.PHONY: LAMP_PULL_AND_START
LAMP_PULL_AND_START:
	docker-compose pull lamp && docker-compose up --build -d lamp

.PHONY: LAMP_START
LAMP_START:
	docker-compose start lamp

.PHONY: LAMP_STOP
LAMP_STOP:
	docker-compose stop lamp

.PHONY: INSTALL
INSTALL: POSTGRE_PULL_AND_START LAMP_PULL_AND_START CELERYBACKEND_PULL_AND_START WORKER_PULL_AND_START FLOWER_PULL_AND_START

.PHONY: START
START: POSTGRE_START LAMP_START WORKER_START CELERYBACKEND_START FLOWER_START

.PHONY: STOP
STOP: LAMP_STOP POSTGRE_STOP WORKER_STOP CELERYBACKEND_STOP FLOWER_STOP

.PHONY: RESTART
RESTART: STOP START

.PHONY: REMOVE_ALL
REMOVE_ALL:
	docker system prune -a
