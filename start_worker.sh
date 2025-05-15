cp .loggingconfig.yaml /worker/lamp;
cd /worker/lamp/celery;
celery -A tasks worker --loglevel=info;
