FROM python:3.11

EXPOSE 80

WORKDIR /Lamp

COPY . /Lamp

RUN cd ./lamp && python3 -m pip install -r requirements.txt

WORKDIR /Lamp/lamp

CMD ["fastapi", "run", "main.py", "--port", "80"]
