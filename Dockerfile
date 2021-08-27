FROM python:latest

WORKDIR /usr/src/app

ENV PLEX_URL http://plex:32400
ENV PLEX_TOKEN ""
COPY preCachePlexEpisode.py .

RUN pip install psutil plexapi

CMD ["python","./preCachePlexEpisode.py"]
