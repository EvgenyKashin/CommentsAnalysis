import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn import linear_model as lm
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import accuracy_score
import re
import pickle
import os
from .models import *


data_path = './data/comments_vrn.csv.gz'
data_app_path = './data_for_app'


def dump_best_data(min_likes=4, max_len=150, min_len=10):
    data = pd.read_csv(data_path)
    best_data = data[(data.likes >= min_likes) & (data.text.str.len() < max_len)\
                     & (data.text.str.len() > min_len)][['text']].reset_index(drop=True)
    
    with open(os.path.join(data_app_path, 'best_comments.pkl'), 'wb') as f:
        pickle.dump(best_data, f)

        
def load_best_data():
    with open(os.path.join(data_app_path, 'best_comments.pkl'), 'rb') as f:
        best_data = pickle.load(f)
    return best_data


def replace_id(df):
    comments_list = []
    for comment in df.text.values:
        c = comment.split()
        if c[0].startswith('[id'):
            c[0] = ''
        c_ = []
        for w in c:
            if w.startswith('id'):
                c_.append('')
            else:
                c_.append(w)
        comments_list.append(' '.join(c))
    comments_list = np.array(comments_list)
    df.text = comments_list


def get_train():
    data = pd.read_csv(data_path)
    
    lenghts_word = np.array([len(m.split()) for m in data.text.values])
    comments = data[(lenghts_word <= 20) & (lenghts_word > 1)]
    without_link = [False if 'http' in c or 'www' in c or '.ru' in c or '.com' in c else True
                    for c in comments.text.values] 
    comments = comments[without_link]

    spam_comments = comments.text.value_counts()[comments.text.value_counts() > 1].keys()
    comments = comments[comments.text.apply(lambda t: t not in spam_comments)]
    comments_list = comments.text.values
    
    replace_id(comments)
    return comments


def make_df_balanced(df, by_col):
    """Make df balanced by binary columns named - by_col. Using oversampling"""
    big_class = 0
    small_class = 1
    if df[by_col].value_counts()[0] < df[by_col].value_counts()[1]:
        big_class = 1
        small_class = 0
    
    delta = df[by_col].value_counts()[big_class] - df[by_col].value_counts()[small_class]
    only_ing = df[df[by_col] == small_class]
    to_add_indexes = np.random.randint(0, len(only_ing) - 1, delta)
    df = pd.concat((df, only_ing.iloc[to_add_indexes]))

    # shuffle after adding
    df = df.iloc[np.random.permutation(df.shape[0])]
    return df


threshold = 0.5

av_model = AverageModel([
    LrModelTfidf('lr_tfidf_5k', 5000, penalty='l2', C=0.2),

    LrModelCount('lr_count_5k_word_12', 5000, ngram_range=(1, 2), penalty='l2', C=0.2),
    LrModelCount('lr_count_10k_word_13', 10000, ngram_range=(1, 3), penalty='l2', C=0.2),

    LrModelCount('lr_count_5k_char_23', 5000, 'char', (2, 3), penalty='l2', C=0.2),
    LrModelCount('lr_count_2k_char_23', 2000, 'char', (2, 3), penalty='l2', C=0.2),
])


def train_model(n_coms=5, train_size=0.9, debug=False):
    comments = get_train()
    unique_ids = comments.from_id.value_counts()[comments.from_id.value_counts() >= n_coms].index.values
    additional_ids = comments.from_id.value_counts()[comments.from_id.value_counts() < n_coms].index.values

    train_idxs = unique_ids[:int(len(unique_ids) * train_size)]
    test_idxs = unique_ids[int(len(unique_ids) * train_size):]

    train_comments = comments[[i in train_idxs for i in comments.from_id]]
    additional_comments = comments[[i in additional_ids for i in comments.from_id]]
    train_comments = pd.concat((train_comments.reset_index(drop=True), additional_comments.reset_index(drop=True)))
    test_comments = comments[[i in test_idxs for i in comments.from_id]]
    # train_comments = make_df_balanced(train_comments, 'is_gum') because class_weight='balanced'

    X_train, X_test = train_comments, test_comments
    y_train, y_test = train_comments.is_gum.values, test_comments.is_gum.values
    
    av_model.fit(X_train, y_train)
    av_model.save(os.path.join(data_app_path, 'av_model.pkl'))

    pr = av_model.predict_proba(X_test)
    score = accuracy_score(y_test, pr > threshold)
    if debug:
        print(score)
    
    
def load_model():
    av_model.load(os.path.join(data_app_path, 'av_model.pkl'))


def predict_one_comment(com):
    com_df = pd.DataFrame([com], columns=['text'])
    return av_model.predict_proba(com_df)


def predict_comments(coms, with_separate=False):
    coms_df = pd.DataFrame(coms, columns=['text'])
    preds = (av_model.predict_proba(coms_df) > threshold).astype(int)
    score = np.median(preds)
    if with_separate:
        return score, preds
    else:
        return score
