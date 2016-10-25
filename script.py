import webbrowser
import pickle
import requests
import json
from datetime import datetime, timedelta
from urllib.parse import parse_qs
import logging
import time
import math
import os

APP_ID = '5298215'
AUTH_FILE = 'auth'
owner_id = '-33041211'

posts_url = "https://api.vk.com/method/wall.get?owner_id={}&"\
            "access_token={}&v=5.52&filter=owner&count={}&offset={}"
comments_url = "https://api.vk.com/method/wall.getComments?owner_id={}&"\
               "post_id={}&need_likes=1&"\
               "access_token={}&v=5.52&count={}&offset={}"
users_url = "https://api.vk.com/method/users.get?user_ids={}&access_token={}&"\
               "fields={}&v=5.52"
auth_url = "https://oauth.vk.com/authorize?client_id={}&scope=wall&"\
           "redirect_uri=https://oauth.vk.com/blank.html&"\
           "display=page&response_type=token"
user_fields = ['sex', 'bdate', 'universities', 'status',
               'counters', 'occupation', 'relation', 'personal', 'activities',
               'interests', 'music', 'movies', 'books', 'can_see_all_posts',
               'can_see_audio', 'can_write_private_message']

posts_path = 'data/posts_{}.pkl'
comments_path = 'data/comments_{}.pkl'
users_path = 'data/users_{}.pkl'


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)
logging.getLogger('requests').setLevel(logging.ERROR)


def get_saved_auth_params():
    access_token = None
    user_id = None
    try:
        with open(AUTH_FILE, 'rb') as pkl_file:
            token = pickle.load(pkl_file)
            expires = pickle.load(pkl_file)
            uid = pickle.load(pkl_file)
        if datetime.now() < expires:
            access_token = token
            user_id = uid
    except IOError:
        pass
    return access_token, user_id


def save_auth_params(access_token, expires_in, user_id):
    expires = datetime.now() + timedelta(seconds=int(expires_in))
    with open(AUTH_FILE, 'wb') as output:
        pickle.dump(access_token, output)
        pickle.dump(expires, output)
        pickle.dump(user_id, output)


def get_auth_params():
    webbrowser.open_new_tab(auth_url.format(APP_ID))
    redirected_url = input("Paste here url you were redirected:\n")
    qs = parse_qs(redirected_url)
    qs['access_token'] = qs.pop(
        'https://oauth.vk.com/blank.html#access_token')
    save_auth_params(qs['access_token'][0], qs['expires_in'][0],
                     qs['user_id'][0])
    return qs['access_token'][0], qs['user_id'][0]


def get_posts(owner_id, token, count=5, offset=0):
    # domain - domain of comunity
    r = requests.get(posts_url.format(owner_id, token, count, offset))
    return json.loads(r.text)


def get_comments(owner_id, post_id, token, count=5, offset=0):
    # domain - domain of comunity
    r = requests.get(comments_url.format(owner_id, post_id, token, count,
                                         offset))
    return json.loads(r.text)


def get_users(user_ids, token, fields):
    url = users_url.format(','.join(str(id) for id in user_ids),
                           token, ','.join(fields))
    try:
        r = requests.get(url)
        users = json.loads(r.text)['response']
    except Exception as ex:
        print("Error: {}".format(r.text))
        print(r)
        raise ex
    return users


def parse_posts(posts, owner_id):
    return [{'post_id': p['id'], 'text': p['text'],
             'likes': p['likes']['count'],
             'date': p['date'], 'owner_id': owner_id} for p in posts]


def parse_comments(comments, owner_id):
    return [{'comment_id': c['id'], 'text': c['text'],
             'likes': c['likes']['count'], 'from_id': c['from_id'],
             'date': c['date'], 'reply_to_uid': c.get('reply_to_uid'),
             'reply_to_cid': c.get('reply_to_cid'),
             'attachments': c.get('attachments'),
             'owner_id': owner_id} for c in comments]


def download_posts(owner_id, token, max_iter=None, suffix='', save=True):
    posts_count = 0
    start_time = time.time()

    logger.info('Downloading posts from {}'.format(owner_id))
    result_posts = []
    post = get_posts(owner_id, token, 1)
    try:
        posts_count = int(post['response']['count'])
    except:
        logger.error(post)
        return
    logger.info('{} total posts'.format(posts_count))
    iteration = math.ceil(posts_count / 100)
    if max_iter:
        iteration = min(max_iter, iteration)

    for i in range(iteration):
        if i % 20 == 0:
            logger.info('{:.2f}%'.format(i / iteration * 100))
        posts = get_posts(owner_id, token, 100, i * 100)
        posts = parse_posts(posts['response']['items'], owner_id)
        result_posts.extend(posts)
        time.sleep(0.33)

    # filterig by date
    min_date = datetime.fromtimestamp(min(result_posts,
                                      key=lambda x: x['date'])['date'])
    logger.debug('Min date: {}'.format(min_date))
    # result_posts = filter_by_date(result_posts, min_date)

    if save:
        filename = posts_path.format(owner_id)
        with open(filename, 'wb') as f:
            pickle.dump(result_posts, f)

    logger.info('{} posts from {} added'.format(len(result_posts),
                owner_id))
    logger.debug('Total time: {} sec'.format(round(time.time() - start_time)))
    return result_posts


def download_comments(posts, owner_id, token, max_iter=None, suffix='',
                      save=True):
    comments_count = 0
    start_time = time.time()
    posts_ids = [p['post_id'] for p in posts]

    logger.info('Downloading comments from {}'.format(owner_id))
    logger.info('{} total posts'.format(len(posts_ids)))
    result_comments = []

    j = 0
    for post_id in posts_ids:
        if j % 500 == 0:
            logger.info('{:.2f}%'.format(j / len(posts_ids) * 100))
            if save:
                filename = comments_path.format(owner_id)
                with open(filename, 'wb') as f:
                    pickle.dump(result_comments, f)
        j += 1

        comment = get_comments(owner_id, post_id, token, 1)
        try:
            comments_count = int(comment['response']['count'])
        except:
            logger.error(comment)
            if comment.get('error', {}).get('error_code', 0) == 5:
                if save:
                    filename = comments_path.format(owner_id)
                    with open(filename, 'wb') as f:
                        pickle.dump(result_comments, f)
                        logger.info('Temporary saved {} comments'
                                    .format(len(result_comments)))
                token, __ = get_auth_params()
            continue
        iteration = math.ceil(comments_count / 100)
        if max_iter:
            iteration = min(max_iter, iteration)

        for i in range(iteration + 1):
            try:
                comments = get_comments(owner_id, post_id, token, 100, i * 100)
                comments = parse_comments(comments['response']['items'],
                                          owner_id)
            except:
                logger.error(comments)
                time.sleep(0.33)
                continue
            result_comments.extend(comments)
            time.sleep(0.33)

    if save:
        filename = comments_path.format(owner_id)
        with open(filename, 'wb') as f:
            pickle.dump(result_comments, f)

    logger.info('{} comments from {} added'.format(len(result_comments),
                owner_id))
    logger.debug('Total time: {} sec'.format(round(time.time() - start_time)))
    return result_comments


def download_users(comments, token, max_iter=None, suffix='', save=True):
    start_time = time.time()
    user_ids = list(set([c['from_id'] for c in comments]))

    logger.info('Downloading users info')
    result_users = []
    logger.info('{} total users'.format(len(user_ids)))
    iteration = math.ceil(len(user_ids) / 10)
    if max_iter:
        iteration = min(max_iter, iteration)

    for i in range(iteration):
        if i % 100 == 0:
            logger.info('{:.2f}%'.format(i / iteration * 100))
        ids = user_ids[10 * i: 10 * (i + 1)]
        if i == iteration - 1:
            ids = user_ids[10 * i:]
        try:
            users = get_users(ids, token, user_fields)
        except:
            time.sleep(20)
            logger.info('Second try')
            users = get_users(ids, token, user_fields)

        result_users.extend(users)
        time.sleep(0.33)

    if save:
        filename = users_path.format(owner_id)
        with open(filename, 'wb') as f:
            pickle.dump(result_users, f)

    logger.info('{} users added'.format(len(result_users)))
    logger.debug('Total time: {} sec'.format(round(time.time() - start_time)))
    return result_users


def read_posts(owner_id, filename=None):
    if not filename:
        if owner_id:
            filename = posts_path.format(owner_id)
        else:
            raise Exception('Wrong arguments')
    with open(filename, 'rb') as f:
        posts = pickle.load(f)
    logger.info('{} posts from {} readed'.format(len(posts), owner_id))
    return posts


def read_comments(owner_id, filename=None):
    if not filename:
        if owner_id:
            filename = comments_path.format(owner_id)
        else:
            raise Exception('Wrong arguments')
    with open(filename, 'rb') as f:
        comments = pickle.load(f)
    logger.info('{} comments from {} readed'.format(len(comments), owner_id))
    return comments


def read_users(owner_id, filename=None):
    if not filename:
        if owner_id:
            filename = users_path.format(owner_id)
        else:
            raise Exception('Wrong arguments')
    with open(filename, 'rb') as f:
        users = pickle.load(f)
    logger.info('{} users from {} readed'.format(len(users), owner_id))
    return users


def main():
    token, user_id = get_saved_auth_params()
    if not token or not user_id:
        token, user_id = get_auth_params()

    posts = None
    comments = None
    if not os.path.exists(posts_path.format(owner_id)):
        posts = download_posts(owner_id, token)
    else:
        posts = read_posts(owner_id)
    if not os.path.exists(comments_path.format(owner_id)):
        comments = download_comments(posts, owner_id, token)
    else:
        comments = read_comments(owner_id)
    if not os.path.exists(users_path.format(owner_id)):
        ok = False
        i = 0
        while not ok:
            try:
                i += 1
                print("{} try".format(i))
                download_users(comments, token)
                ok = True
            except:
                continue
    logger.info('Done')

if __name__ == '__main__':
    main()
