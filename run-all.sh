#!/bin/sh
cd kafka; docker-compose up -d; cd ..;
cd api_call; docker build -t apicall-image .; docker run -d --name apicall-container -p 5002:5002 apicall-image; cd ..;
docker network connect kafka_default apicall-container;
cd frontend; docker build -t frontend-image .; docker-compose up -d; cd ..;
