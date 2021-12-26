FROM python:3.8

COPY . /api_call

WORKDIR /api_call

RUN pip install -r requirements.txt

CMD ["python", "-u", "api_check.py"]