FROM python:3.8

COPY . /broker2

WORKDIR /broker2

RUN pip install -r requirements.txt

CMD ["python", "-u", "broker2.py"]