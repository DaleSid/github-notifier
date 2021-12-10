## CSE-586-Project2 - Pub/Sub Implementation with Kafka

```
Team number : 78
Topic : Github Daily Notification System
Members : Siddharth Sankaran(50421657), Shriram Ravi (50419944)
Project : 2 - Pub/Sub Implementation with Kafka
```

# **Repo link**:
`https://github.com/DaleSid/CSE-586-Project1`

The purpose of this document is to provide the reader with an understanding of the project and a brief walkthrough of the necessary steps required to run the code successfully

# **Scope**: 
The pub/sub system that will be built will act as a daily GitHub Daily notification system. Users can subscribe to any open repository on Github and will receive a daily update of all the commits in that repo.

# **Project 2**: 
We have implemented an extensive frontend webpage and a fullfledged middleware that runs is basically a set of Kafka brokers. The frontend  flask webpage takes input - Username, Owner of repo, name of repository. These inputs are collectively considered as a topic. The topics to which a consumer has subscribed is polled seeking messages from Kafka message broker cluster. Then the API calls fetches the data from the data providers regarding the subscribed topic. These are then sent over(Produced) to the Kafka message broker clusters according to their topics. Kafka does all the other parts in the background like collating the messages, maintaining the partitions(Message queue like structures), data replication and data delivery. 

Please find below the steps to be followed to obtain a successful implementation of Project 2

1) In Terminal, navigate to the kafka folder and run the following command
- `docker-compose up -d`
- This will create separate container for Zookeeper, Kafka message broker cluster and initiate it. This container will be placed under a docker network.

2) In another terminal, navigate to the api_call folder and run the following command
- `docker build -t apicall-image .`
- `docker run --name apicall-container -p 5002:5002 apicall-image`
- This will create a container designed for fetching publishers data from the GitHub

3) Connect the API Data provider to the same docker network
- `docker network connect kafka_default apicall-container`

4) In another Terminal, navigate to frontend folder and run to create the frontend docker image
- `docker build -t frontend-image .` 
  
5) Use the image to create the front end container
- `docker-compose up -d`
- This creates ten instances of the front-end image. You can extend this and create multiple instances of front end containers (Subscribers). These needs to be exposed to different local ports. Get the list of ports in which the front end containers are running so that we could access it later. We consider 6003 as one of the ports.
  
6) To verify if all three containers are in the same network run,
- `docker network inspect kafka_default`

7) Open a browser and go to 
- `localhost:5002`
- This will start the data fetcher container and publish/produce the appropriate GitHub events to the Kafka cluster
- You can add topics to the system by going to `localhost:5002/addtopics` and provide appropriate inputs.
  
8) Open a browser and go to 
- `localhost:5003`
- Provide apporpriate inputs. These inputs will be considered as a topic and polled for messages from Kafka cluster.
- This is extensible to all the containers created with the frontend-image

9) If you don't want any hassle running all the above commands, just `cd` to the project directory and run
- `./run-all.sh`