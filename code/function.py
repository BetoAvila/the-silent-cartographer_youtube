import csv
from googleapiclient.discovery import build
from dotenv import load_dotenv, find_dotenv
from datetime import datetime
from llama_cpp import Llama
import pandas as pd
import sys
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
    load_dotenv(find_dotenv())
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


def ai_evaluate(comment: str, lang: str) -> str:
    llama2_model = Llama(model_path='ggml-model-q4_0.gguf',
                         verbose=False,
                         n_ctx=512)
    eng_prompt = 'Please provide a single word to evaluate the following comment. ' + \
        'Use "Positive" for nice comments, "Negative" for mean or rude comments ' + \
            f'or "None" when a comment does not fall on either 2 previous categories: {comment}'
    spa_prompt = f'Evalúa el comentario con una sola palabra. ' + \
        '"Positive" para comentarios agradables o buenos, "Negative" para comentarios desagradables o agresivos ' + \
        f'y "Nulo" para cuando el comentario no corresponda a las opciones anteriores: {comment}'
    if lang == 'eng': prompt = eng_prompt
    elif lang == 'spa': prompt = spa_prompt
    output = llama2_model.create_chat_completion(messages=[{
        'role': 'user',
        'content': prompt
    }],
                                                 max_tokens=324)
    return output['choices'][0]['message']['content']


def analyze_comments(url: str, lang: str) -> pd.DataFrame:
    """Wraper function to get data recursively if comments exceed 100
    and stores them in a `pd.DataFrame` with the features:
    ```
    'video_id', 'comment_id', 'textOriginal', 'authorDisplayName',
    'authorChannelUrl', 'likeCount', 'publishedAt', 'updatedAt'
    ```
    Check `get_comments_data()` docstring for further details.
    
    ---
    Args:
        - `url` (str):
            YouTube URL video with the format: 
            `https://www.youtube.com/watch?v=xxxxxxxxx`.
        - `lang` (str):
            Language of the YouTube video and comments to AI-evaluate.
    ---
    Returns:
        - `df` (pd.DataFrame | None):
            Df that stores comments data.
    """
    df, tkn = None, None
    while (True):
        url, df, tkn = get_comments_data(url, df, tkn)
        if tkn is None: break
    df.publishedAt = pd.to_datetime(df.publishedAt,
                                    format='%Y-%m-%dT%H:%M:%SZ')
    df.updatedAt = pd.to_datetime(df.updatedAt, format='%Y-%m-%dT%H:%M:%SZ')
    df.rename(columns={
        'textOriginal': 'comment',
        'authorDisplayName': 'comment_author',
        'authorChannelUrl': 'author_url',
        'likeCount': 'comment_like_count',
        'publishedAt': 'published_at',
        'updatedAt': 'updated_at'
    },
              inplace=True)
    df['AI_evaluation'] = df.comment.apply(ai_evaluate, lang=lang)
    csv_name = f'result_{datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}_{url.split("=")[-1]}.csv'
    df.to_csv(csv_name, sep='|', index=False)
    print(
        f'Finished analyzing video comments and results are summarized in the file: {csv_name}'
    )


if __name__ == '__main__':
    analyze_comments(url=sys.argv[1], lang=sys.argv[2])
