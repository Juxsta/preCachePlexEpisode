#######################################
# This python script should be run
# as a cron job every 15 minutes to
# cache the next episode of a currently
# playing TV show. 
########################################

import requests
import os
import psutil
from plexapi.server import PlexServer, CONFIG
from plexapi.exceptions import NotFound
from plexapi.video import Episode

PLEX_URL = 'http://127.0.0.1:32400'
PLEX_TOKEN = ''

if not PLEX_URL:
    PLEX_URL = CONFIG.data['auth'].get('server_baseurl')
if not PLEX_TOKEN:
    PLEX_TOKEN = CONFIG.data['auth'].get('server_token') 

plex = PlexServer(PLEX_URL, PLEX_TOKEN)
currentlyPlaying = plex.sessions()


for episode in currentlyPlaying:
    if isinstance(episode, Episode):
        show = episode.grandparentTitle
        seasonNumber = episode.parentIndex
        filename = episode.media[0].parts[0].file
        episodeNumber = episode.index
        print("Show: " + show)
        print("Season: " + str(seasonNumber))
        print("Ep Num: " + str(episodeNumber))

        def nextEpisode(show, seasonNumber, episodeNumber):
            episodes = plex.library.section('TV Shows').get(show).episodes()
            try:
                index = next(i for i, ep in enumerate(episodes) if ep.seasonNumber == seasonNumber and ep.episodeNumber == episodeNumber)
                return episodes[index + 1]
            except StopIteration:
                raise NotFound
            except IndexError:
                # already last episode
                pass

        res = nextEpisode(show, int(seasonNumber), int(episodeNumber))
        nextEp = nextEpisode(show, int(seasonNumber), int(episodeNumber))
        fileToCache = nextEp.media[0].parts[0].file
        print("Next ep is " + fileToCache)
        startCache = 1
        for proc in psutil.process_iter():
            if proc.name() in 'rclone':
              if proc.cmdline()[1] in 'md5sum':
               if proc.cmdline()[4] in fileToCache: 
                 print("File is already being cached: " + fileToCache)
                 startCache = 0
        if startCache == 1:
          print("Starting cache of " + fileToCache)
          bashCommand = "nohup rclone md5sum --checkers 8 '" + fileToCache + "' &"      
          os.system(bashCommand)