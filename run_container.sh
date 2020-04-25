#!/bin/bash
# Stop and remove current newsbot instance
docker stop newsbot;
docker rm newsbot;

# Start a new newsbot instance
docker run --name newsbot -v $1:/resources -v $2:/data -d newsbot:latest;
