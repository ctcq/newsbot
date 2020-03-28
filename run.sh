docker build -t newsfeed_bot .
docker run -it --rm --name nb -v /root/newsfeed_bot:/opt/newsfeed_bot newsfeed_bot python /opt/newsfeed_bot/src/main.py