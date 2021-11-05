FROM python:3.8

COPY . /broker3

WORKDIR /broker3

RUN pip install -r requirements.txt

CMD ["python", "-u", "broker3.py"]