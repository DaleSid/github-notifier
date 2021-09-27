# CSE-586-Project1 - Pub/Sub Implementation

```Team number : 78
Topic : Github Daily Notification System
Members : Siddharth Sankaran(50421657), Shriram Ravi (50419944)
Phase I - Container Technology Docker```

The purpose of this document is to provide the reader with an understanding of the project and a brief walkthrough of the necessary steps required to run the code successfully

Scope: The pub/sub system that will be built will act as a daily GitHub Daily notification system. Users can subscribe to any open repository on Github and will receive a daily update of all the commits in that repo.

For Phase 1, we have implemented the a simple frontend webpage and a portion of the middleware. The frontend  flask webpage takes input - Username, Owner of repo, name of repository. This is sent to the middle ware flask server which pushes the information onto a MongoDB database. The project is implemented with two containers, one for the frontend and one for the middleware and MongoDB

Please find below the steps to be followed to obtain a successful implementation of Phase 1 of the project
1. In Terminal, navigate to frontend folder and run to create the frontend docker image
		~ docker build -t frontend-image . 

2. Use the image to create the front end container
        ~ docker run --name frontend-container -p 5000:5000 frontend-image

3. This will run the frontend container on port 5000 in localhost

4. In another terminal, navigate to the backend folder and run the following command
        ~ docker-compose up
    This will create separate containers for the middleware (flask server) and the backend (MongoDB) and initiate them. Both these containers are placed in a docker network

5. In another terminal, run the following command to add the front end container to the above docker network so that all three containers are in the same network
        ~ docker network connect backend_default frontend-container

6. To verify if all three containers are in the same network run,
        ~ docker network inspect backend_default

7. Open a browser and go to 
        ~ localhost:5000
    Provide apporpriate inputs. These inputs will be added to the MongoDB once the submit button is clicked

8. Visit the below webpage to view the added entries
        ~ localhost:5001/viewtable