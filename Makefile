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

POSTGRE_PULL_AND_START:
	docker-compose pull && docker-compose up -d

POSTGRE_START:
	docker-compose start

POSTGRE_STOP:
	docker-compose stop

REMOVE_ALL:
	docker system prune -a
