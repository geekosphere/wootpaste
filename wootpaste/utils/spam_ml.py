# -*- coding: utf-8 -*-
# simple spam detection using scikit-learn

import cPickle as pickle

from wootpaste.config import config

from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.naive_bayes import BernoulliNB, MultinomialNB
from sklearn.linear_model import SGDClassifier
from sklearn.pipeline import Pipeline
from sklearn.cross_validation import KFold

from wootpaste.database import db_session
from wootpaste.models import Paste

import logging
logger = logging.getLogger('wootpaste')

HAM = 0
SPAM = 1
model = Pipeline([
    ('vectorizer',  CountVectorizer(ngram_range=(1, 2))),
    ('tfidf_transformer',  TfidfTransformer()),
    ('classifier',  SGDClassifier()) ])

from os.path import join, dirname, abspath
model_file = join(dirname(abspath(__file__)), '../..', 'paste_spam_model')

def load_dataset():
    """Loads a dataset for training and testing: returns a (X,y) tuple."""
    data = [(x.id, x.content, HAM) for x in Paste.query.filter_by(spam=False).all()]\
         + [(x.id, x.content, SPAM) for x in Paste.query.filter_by(spam=True).all()]
    return ([x[1] for x in data], [x[2] for x in data])

def train():
    """Trains and caches the resulting model."""
    X, y = load_dataset()
    model.fit(X, y)
    pickle.dump(model, open(model_file, 'w'))

def load():
    """Loads a pre-trained model."""
    global model
    logger.info('spam_ml loads a model')
    try:
        model = pickle.load(open(model_file, 'r'))
        logger.info('spam_ml finished loading model')
    except:
        logger.info('spam_ml error not loaded')

def predict(content):
    """Predicts if content is spam or not."""
    r = model.predict((content, ))
    logger.info('spam_ml predict content: ' + str(r))
    return r[0]

def evaluate():
    """Performs a cross-validation using kfold."""
    X, y = load_dataset()
    k_fold = KFold(n=len(X), n_folds=6, indices=True, shuffle=True)
    scores = []
    for train_indices, test_indices in k_fold:
        train_X = [X[i] for i in train_indices]
        train_y = [y[i] for i in train_indices]

        test_X = [X[i] for i in test_indices]
        test_y = [y[i] for i in test_indices]

        model.fit(train_X, train_y)
        score = model.score(test_X, test_y)
        print 'Fold iteration, score=' + str(score)
        scores.append(model.score(test_X, test_y))
    return sum(scores) / len(scores)



