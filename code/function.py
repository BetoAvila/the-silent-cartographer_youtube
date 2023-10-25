from googleapiclient.discovery import build
from dotenv import load_dotenv
import pandas as pd
import os


def get_comments_data(url: str | None, df: pd.DataFrame | None,
                      tkn: str | None) -> tuple[str, pd.DataFrame, str]:
    """Function to build table with comments data. Given a YT url,
    grab all top comments in the comment section from that video, and
    stores them in a `pd.DataFrame` with the features:
    ```
    'video_id', 'comment_id', 'textOriginal', 'authorDisplayName',
    'authorChannelUrl', 'likeCount', 'publishedAt', 'updatedAt'
    ```
    YT API limits responses to 100 comments max, so in case a video has
    more, it provides a token to point to the next batch of comments.
    YT API response is expected as follows:
    ```
    {
        "nextPageToken":"11223344",
        "items": [
            {
                "id": "UgxWutYSXLLPWaReIy54AaABAg",
                "snippet": {
                    "topLevelComment": {
                        "snippet": {
                            "textOriginal": "Thanks for explaining this topic in a way that a person without a data background could understand.",
                            "authorDisplayName": "रोहन",
                            "authorChannelUrl": "http://www.youtube.com/channel/UCTD_GM0OJuZ1OBPTeQtJbJA",
                            "likeCount": 0,
                            "publishedAt": "2023-10-23T06:31:01Z",
                            "updatedAt": "2023-10-23T06:31:01Z"
                        }
                    }
                }
            },
            {
                "id": "UgxiHAcD6HM8CGBHFLd4AaABAg",
                "snippet": {
                    "topLevelComment": {
                        "snippet": {
                            "textOriginal": "Well explained. Easy to understand.",
                            "authorDisplayName": "Rajat Mishra",
                            "authorChannelUrl": "http://www.youtube.com/channel/UCCfg-aU6syh6Dp6kBZlU5Sg",
                            "likeCount": 0,
                            "publishedAt": "2023-10-23T03:01:14Z",
                            "updatedAt": "2023-10-23T03:01:14Z"
                        }
                    }
                }
            }
        ]
    }
    ```
    ---
    Args:
        - `url` (str | None):
            YouTube URL video with the format: 
            `https://www.youtube.com/watch?v=xxxxxxxxx`.
        - `df` (pd.DataFrame | None): 
            Df that stores comments data.
        - `tkn` (str | None): 
            API token that points to the next batch of comments response
    ---
    Returns:
        - `tuple[str, pd.DataFrame, str]`: 
            `url`, `df` and `tkn` Same variables given that this function
            can work recursively.
    """
    comments_cols = [
        'video_id', 'comment_id', 'textOriginal', 'authorDisplayName',
        'authorChannelUrl', 'likeCount', 'publishedAt', 'updatedAt'
    ]
    url = url.split('=')[-1]
    load_dotenv('.env')
    api_key = os.getenv('YT_API_KEY')
    if tkn is None:  # First 100 comments batch
        with build('youtube', 'v3', developerKey=api_key) as yt_service:
            request = yt_service.commentThreads().list(
                part='snippet',
                videoId=url,  #'uvTl6GefR9o',
                pageToken=None,
                maxResults=100,
                fields=
                'nextPageToken,items(id,snippet(topLevelComment(snippet(textOriginal,authorDisplayName,authorChannelUrl,likeCount,publishedAt,updatedAt))))'
            )
            data = request.execute()
    else:  # Next 100 comments batch
        with build('youtube', 'v3', developerKey=api_key) as yt_service:
            request = yt_service.commentThreads().list(
                part='snippet',
                videoId=url,  #'qJsFgPpKwE0',
                pageToken=tkn,
                maxResults=100,
                fields=
                'nextPageToken,items(id,snippet(topLevelComment(snippet(textOriginal,authorDisplayName,authorChannelUrl,likeCount,publishedAt,updatedAt))))'
            )
            data = request.execute()
    tkn = data.get('nextPageToken', None)
    comments = [
        data['items'][i]['snippet']['topLevelComment']['snippet'] | {
            'comment_id': data['items'][i]['id']
        } for i in range(len(data['items']))
    ]
    if df is None:  # First 100 comments batch
        df = pd.DataFrame(comments)
        df['video_id'] = url
    else:  # Next 100 comments batch
        x = pd.DataFrame(comments)
        x['video_id'] = url
        df = pd.concat([df, x], ignore_index=True)
    return 'https://www.youtube.com/watch?v=' + url, df[comments_cols], tkn


def get_comments(url: str) -> pd.DataFrame:
    """Wraper function to get data recursively if comments exceed 100
    and stores them in a `pd.DataFrame` with the features:
    ```
    'video_id', 'comment_id', 'textOriginal', 'authorDisplayName',
    'authorChannelUrl', 'likeCount', 'publishedAt', 'updatedAt'
    ```
    Check `get_comments_data()` docstring for further details.
    
    ---
    Args:
        - `url` (str | None):
            YouTube URL video with the format: 
            `https://www.youtube.com/watch?v=xxxxxxxxx`.
    ---
    Returns:
        - `df` (pd.DataFrame | None):
            Df that stores comments data.
    """
    df, tkn = None, None
    while (True):
        url, df, tkn = get_comments_data(url, df, tkn)
        if tkn is None: break
    return df


# TODO create videos table, variables of video:
# id, publishedAt, title, description, duration, viewCount, likeCount, dislikeCount
# TODO optimize pandas dfs datatypes
# TODO implement llama2

# test API: https://developers.google.com/youtube/v3/docs
# API git repo: https://github.com/googleapis/google-api-python-client/blob/main/docs/start.md
# API docs: https://developers.google.com/resources/api-libraries/documentation/youtube/v3/python/latest/index.html
