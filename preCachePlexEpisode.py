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

PLEX_URL = os.environ['PLEX_URL']
PLEX_TOKEN = os.environ['PLEX_TOKEN']

if not PLEX_URL:
    PLEX_URL = CONFIG.data['auth'].get('server_baseurl')
if not PLEX_TOKEN:
    PLEX_TOKEN = CONFIG.data['auth'].get('server_token')

session = requests.Session()
session.verify = False

plex = PlexServer(PLEX_URL, PLEX_TOKEN,session)
currentlyPlaying = plex.sessions()


for episode in currentlyPlaying:
    if isinstance(episode, Episode):
        show = episode.grandparentTitle
        seasonNumber = episode.parentIndex
        filename = episode.media[0].parts[0].file
        episodeNumber = episode.index
        episodeSection = episode.librarySectionTitle
        print("Show: " + show)
        print("Season: " + str(seasonNumber))
        print("Ep Num: " + str(episodeNumber))

        def nextEpisode(show, seasonNumber, episodeNumber):
            episodes = plex.library.section(episodeSection).get(show).episodes()
            try:
                index = next(i for i, ep in enumerate(episodes) if ep.seasonNumber == seasonNumber and ep.episodeNumber == episodeNumber)
                return episodes[index + 1]
            except StopIteration:
                raise NotFound
            except IndexError:
                # already last episode
                pass

        nextEp = nextEpisode(show, int(seasonNumber), int(episodeNumber))
        
        try:
           fileToCache = nextEp.media[0].parts[0].file
           print("Next ep is " + fileToCache)
           startCache = 1
        except:
            print("No file found to cache. Possibly last available episode?")
            startCache = 0
           
        if startCache == 1 and fileToCache:    
          for proc in psutil.process_iter():
              if proc.name() in 'rclone':
                if proc.cmdline()[1] in 'md5sum':
                 if proc.cmdline()[2] in fileToCache: 
                     print("File is already being cached: " + fileToCache)
                     startCache = 0
                     
        if startCache == 1 and fileToCache:                
          print("Starting cache of " + fileToCache)
          bashCommand = 'nohup rclone md5sum "' + fileToCache + '" &'      
          os.system(bashCommand)