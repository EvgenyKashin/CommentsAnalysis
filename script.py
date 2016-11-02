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
vrn_id = '-33041211'
spb_id = '-31516466'
my_id = '68095528'

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
friends_url = "https://api.vk.com/method/friends.get?user_id={}&"\
              "&access_token={}&fields={}&count={}&offset={}&v=5.52"
user_fields = ['sex', 'bdate', 'universities', 'status',
               'counters', 'occupation', 'relation', 'personal', 'activities',
               'interests', 'music', 'movies', 'books', 'can_see_all_posts',
               'can_see_audio', 'can_write_private_message']
friend_fields = []

posts_path = 'data/posts_{}.pkl'
comments_path = 'data/comments_{}.pkl'
users_path = 'data/users_{}.pkl'
friends_path = 'data/friends_{}.pkl'
frinds_comments_path = 'data/fr_com_{}_{}.pkl'

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
    r = requests.get(posts_url.format(owner_id, token, count, offset))
    return json.loads(r.text)


def get_comments(owner_id, post_id, token, count=5, offset=0):
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


def get_friends(user_id, token, count=100, offset=0, fields=friend_fields):
    url = friends_url.format(user_id, token, count, ','.join(fields), offset)
    r = requests.get(url)
    return json.loads(r.text)


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


def parse_friends(friends):
    return [{'first_name': f['first_name'], 'last_name': f['last_name'],
             'id': f['id']} for f in friends]


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


def download_users(comments, token, owner_id, max_iter=None, suffix='',
                   save=True):
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
        if i == iteration - 1:
            ids = user_ids[10 * i:]
        else:
            ids = user_ids[10 * i: 10 * (i + 1)]
        try:
            users = get_users(ids, token, user_fields)
        except Exception as ex:
            time.sleep(20)
            print(ex)
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


def download_friends(user_id, token, max_iter=None, suffix='', save=True):
    friends_count = 0
    start_time = time.time()

    logger.info('Downloading friends from {}'.format(user_id))
    result_friends = []
    friend = get_friends(user_id, token, 1)
    try:
        friends_count = int(friend['response']['count'])
    except:
        logger.error(friend)
        return
    logger.info('{} total friends'.format(friends_count))
    iteration = math.ceil(friends_count / 100)
    if max_iter:
        iteration = min(max_iter, iteration)

    for i in range(iteration):
        if i % 1 == 0:
            logger.info('{:.2f}%'.format(i / iteration * 100))
        friends = get_friends(user_id, token, 100, i * 100)
        friends = parse_friends(friends['response']['items'])
        result_friends.extend(friends)
        time.sleep(0.33)

    if save:
        filename = friends_path.format(user_id)
        with open(filename, 'wb') as f:
            pickle.dump(result_friends, f)

    logger.info('{} friends of {} added'.format(len(result_friends),
                user_id))
    logger.debug('Total time: {} sec'.format(round(time.time() - start_time)))
    return result_friends


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


def read_friends(user_id, filename=None):
    if not filename:
        if user_id:
            filename = friends_path.format(user_id)
        else:
            raise Exception('Wrong arguments')
    with open(filename, 'rb') as f:
        friends = pickle.load(f)
    logger.info('{} friends of {} readed'.format(len(friends), user_id))
    return friends


def friends_comments(user_id, community_id, save=True):
    start_time = time.time()
    logger.info('Searching comments in {} from friends of {}'
                .format(community_id, user_id))

    friends = read_friends(user_id)
    comments = read_comments(community_id)
    users_ids_in_com = set([c['from_id'] for c in comments])

    friends_with_com = []
    for friend in friends:
        if friend['id'] in users_ids_in_com:
            users_com = [c for c in comments if c['from_id'] == friend['id']]
            friends_with_com.append({'user': friend,
                                     'comments': users_com})

    if save:
        filename = frinds_comments_path.format(user_id, community_id)
        with open(filename, 'wb') as f:
            pickle.dump(friends_with_com, f)

    logger.info('{} friends commented in this community'
                .format(len(friends_with_com)))
    logger.debug('Total time: {} sec'.format(round(time.time() - start_time)))
    return friends_with_com


def read_friends_comments(user_id, community_id, filename=None):
    if not filename:
        if user_id and community_id:
            filename = frinds_comments_path.format(user_id, community_id)
        else:
            raise Exception('Wrong arguments')
    with open(filename, 'rb') as f:
        friends_comments = pickle.load(f)
    logger.info('{} friends comments readed'.format(len(friends_comments)))
    return friends_comments


def friends_comments_filter(fr_com, last_name):
    return [f for f in fr_com if f['user']['last_name'] == last_name]


def friends_comments_names(fr_com):
    return [f['user']['last_name'] for f in fr_com]


def community_downloader(owner_id, with_users=True):
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
    if not os.path.exists(users_path.format(owner_id)) and with_users:
        ok = False
        i = 0
        while not ok:
            try:
                i += 1
                print("{} try".format(i))
                download_users(comments, token, owner_id)
                ok = True
            except:
                continue
    logger.info('Done')


def user_downloader(owner_id):
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
    logger.info('Done')


if __name__ == '__main__':
    # user_downloader(my_id)
    community_downloader(spb_id, True)
    # friends_comments(my_id, owner_id)
    pass
