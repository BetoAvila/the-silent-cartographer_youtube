from googleapiclient.discovery import build
import yaml

with open('./code/config.yaml', 'r') as f:
    api_key = yaml.safe_load(f)['youtube']['API_KEY']
with build('youtube', 'v3', developerKey=api_key) as yt_service:
    request = yt_service.commentThreads().list(
        part='snippet',
        videoId='qJsFgPpKwE0',
        maxResults=100,
    )
    d = request.execute()
total_comments = d['pageInfo']['totalResults']
comments = [
    d['items'][i]['snippet']['topLevelComment']['snippet']['textOriginal']
    for i in range(total_comments)
]
print(total_comments, comments)

# TODO organize data pulled from method (2 tables created: videos, comments)
# variables of video:
# id, publishedAt, title, description, duration, viewCount, likeCount, dislikeCount
# variables of comments:
# d['items'][i]['snippet']['topLevelComment']['snippet']['textOriginal']
# d['items'][i]['snippet']['topLevelComment']['snippet']['authorDisplayName']
# d['items'][i]['snippet']['topLevelComment']['snippet']['authorChannelUrl']
# d['items'][i]['snippet']['topLevelComment']['snippet']['likeCount']
# d['items'][i]['snippet']['topLevelComment']['snippet']['publishedAt']
# d['items'][i]['snippet']['topLevelComment']['snippet']['updatedAt']

# TODO check swarm and secrets
