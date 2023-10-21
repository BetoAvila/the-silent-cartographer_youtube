# https://stackoverflow.com/questions/19965856/how-to-get-all-comments-on-a-youtube-video
from googleapiclient.discovery import build
import yaml

with open('./code/config.yaml', 'r') as f:
    api_key = yaml.safe_load(f)['youtube']['API_KEY']
with build('youtube', 'v3', developerKey=api_key) as yt_service:
    yt_service
# TODO pull comments from commentsthread method
# TODO organize data pull from method
