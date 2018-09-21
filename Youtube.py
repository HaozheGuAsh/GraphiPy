#!/usr/bin/python

import httplib2
import os
import sys

from apiclient.discovery import build_from_document
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run_flow

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def get_comments(youtube, video_id, channel_id):
    results = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        channelId=channel_id,
        textFormat="plainText"
    ).execute()

    # for item in results["items"]:
    # comment = item["snippet"]["topLevelComment"]
    # author = comment["snippet"]["authorDisplayName"]
    # text = comment["snippet"]["textDisplay"]

    # print("Comment by %s: %s" % (author, text))
    # for y in comment["snippet"]:
    #   print (y, ':', comment["snippet"][y])

    return results["items"]


# Remove keyword arguments that are not set
def remove_empty_kwargs(**kwargs):
    good_kwargs = {}
    if kwargs is not None:
        for key, value in kwargs.iteritems():
            if value:
                good_kwargs[key] = value
    return good_kwargs


def build_resource(properties):
    resource = {}
    for p in properties:
        # Given a key like "snippet.title", split into "snippet" and "title", where
        # "snippet" will be an object and "title" will be a property in that object.
        prop_array = p.split('.')
        ref = resource
        for pa in range(0, len(prop_array)):
            is_array = False
            key = prop_array[pa]

            # For properties that have array values, convert a name like
            # "snippet.tags[]" to snippet.tags, and set a flag to handle
            # the value as an array.
            if key[-2:] == '[]':
                key = key[0:len(key) - 2:]
                is_array = True

            if pa == (len(prop_array) - 1):
                # Leave properties without values out of inserted resource.
                if properties[p]:
                    if is_array:
                        ref[key] = properties[p].split(',')
                    else:
                        ref[key] = properties[p]
            elif key not in ref:
                # For example, the property is "snippet.title", but the resource does
                # not yet have a "snippet" object. Create the snippet object here.
                # Setting "ref = ref[key]" means that in the next time through the
                # "for pa in range ..." loop, we will be setting a property in the
                # resource's "snippet" object.
                ref[key] = {}
                ref = ref[key]
            else:
                # For example, the property is "snippet.description", and the resource
                # already has a "snippet" object.
                ref = ref[key]
    return resource


def print_response(response):
    print(response)


class Channel:
    def __init__(self, channel):
        self.channel_id = channel['id']['channelId']
        self.channel_title = channel['snippet']['title']
        self.description = channel['snippet']['description']


class Video:
    def __init__(self, video):
        self.published_at = video['snippet']['publishedAt']
        self.video_id = video['id']['videoId']
        self.title = video['snippet']['title']
        self.description = video['snippet']['description']

        # relational
        self.channel_id = video['snippet']['channelId']
        self.channel_title = video['channelTitle']


class Playlist:
    def __init__(self, playlist):
        self.published_at = playlist['snippet']['publishedAt']
        if playlist['id']['playlistId'] is None:
            self.playlist_id = playlist['id']
        else:
            self.playlist_id = playlist['id']['playlistId']
        self.title = playlist['snippet']['title']
        self.description = playlist['snippet']['description']

        # relational
        self.channel_id = playlist['snippet']['channelId']
        self.channel_title = playlist['channelTitle']


class Comment:
    def __init__(self, comment):
        # Attributes:
        self.updated_at = comment['snippet']['updatedAt']
        self.published_at = comment['snippet']['publishedAt']
        self.view_rating = comment['snippet']['viewerRating']
        self.can_rate = comment['snippet']['canRate']
        self.text_original = comment['snippet']['textOriginal']
        self.text_display = comment['snippet']['textDisplay']
        self.like_count = comment['snippet']['likeCount']

        # Relational Attributes:
        self.video_id = comment['snippet']['videoId']
        self.author_channel_id = comment['snippet']['authorChannelId']['value']
        self.author_channel_url = comment['snippet']['authorChannelUrl']
        self.author_display_name = comment['snippet']['authorDisplayName']


class Youtube:
    def __init__(self, api):
        self.YOUTUBE_READ_WRITE_SSL_SCOPE = "https://www.googleapis.com/auth/youtube.force-ssl"
        self.YOUTUBE_API_SERVICE_NAME = 'youtube'
        self.YOUTUBE_API_VERSION = 'v3'
        self.DEVELOPER_KEY = api["api_key"]
        self.CLIENT_SECRET_FILE = api["client_secret"]
        # This variable defines a message to display if the CLIENT_SECRETS_FILE is
        # missing.
        self.MISSING_CLIENT_SECRET_MESSAGE = """
        WARNING: Please configure OAuth 2.0
        
        To make this sample run you will need to populate the client_secrets.json file
        found at:
           %s
        with information from the APIs Console
        https://console.developers.google.com
        
        For more information about the client_secrets.json file format, please visit:
        https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
        """ % os.path.abspath(os.path.join(os.path.dirname(__file__), self.CLIENT_SECRET_FILE))

        self.videos = []
        self.channels = []
        self.playlists = []
        self.video_comments = []
        self.youtube = build(self.YOUTUBE_API_SERVICE_NAME, self.YOUTUBE_API_VERSION,
                             developerKey=self.DEVELOPER_KEY)

    # Authorize the request and store authorization credentials.
    def get_authenticated_service(self, args):
        flow = flow_from_clientsecrets(self.CLIENT_SECRET_FILE, scope=self.YOUTUBE_READ_WRITE_SSL_SCOPE,
                                       message=self.MISSING_CLIENT_SECRET_MESSAGE)

        storage = Storage("%s-oauth2.json" % sys.argv[0])
        credentials = storage.get()

        if credentials is None or credentials.invalid:
            credentials = run_flow(flow, storage, args)

        # Trusted testers can download this discovery document from the developers page
        # and it should be in the same directory with the code.
        with open("youtube-v3-discoverydocument.json", "r") as f:
            doc = f.read()
            return build_from_document(doc, http=credentials.authorize(httplib2.Http()))

    # Call the API's commentThreads.list method to list the existing comments.

    def youtube_search(self, options):

        # Call the search.list method to retrieve results matching the specified
        # query term.
        search_response = self.youtube.search().list(
            q=options.q,
            part='id,snippet',
            maxResults=options.max_results
        ).execute()

        # Add each result to the appropriate list, and then display the lists of
        # matching videos, channels, and playlists.
        try:
            for search_result in search_response.get('items', []):

                if search_result['id']['kind'] == 'youtube#video':
                    self.videos.append(Video(search_result))
                    self.video_comments.append(get_comments(self.youtube, search_result['id']['videoId'], None))

                elif search_result['id']['kind'] == 'youtube#channel':
                    self.channels.append(Channel(search_result))
                    self.video_comments.append(get_comments(self.youtube, None, search_result['id']['channelId']))

                elif search_result['id']['kind'] == 'youtube#playlist':
                    playlistId = search_result['id']['playlistId']
                    self.playlists.append(
                        '%s (%s)' % (search_result['snippet']['title'], playlistId))
                    self.playlist_items_list_by_playlist_id(part='snippet,contentDetails',
                                                            maxResults=25,
                                                            playlistId=playlistId)

        except HttpError as e:
            print("An HTTP error %d occurred:\n%s" % (e.resp.status, e.content))

    # Build a resource based on a list of properties given as key-value pairs.
    # Leave properties with empty values out of the inserted resource.

    def playlist_items_list_by_playlist_id(self, **kwargs):
        # See full sample for function
        kwargs = remove_empty_kwargs(**kwargs)

        response = self.youtube.playlistItems().list(
            **kwargs
        ).execute()

        self.playlists.append(response['items'])

    def pretty_print(self):
        print('Videos:\n', '\n'.join(self.videos), '\n')
        print('Channels:\n', '\n'.join(self.channels), '\n')
        print('Playlist:\n', '\n'.join(self.playlists), '\n')
        print('Playlist:\n', '\n'.join(self.video_comments), '\n')
