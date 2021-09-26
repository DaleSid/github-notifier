FROM python:3.8

COPY . /middleflask

WORKDIR /middleflask 

RUN pip install -r requirements.txt

ENTRYPOINT [ "python" ]
CMD [ "app.py" ]