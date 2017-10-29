import numpy as np
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn import linear_model as lm
import pickle


class Model:
    def __init__(self, name='-'):
        self.name = name
        
    def fit(self, X, y):
        raise NotImplemented()
    
    def predict(self, X):
        raise NotImplemented()
    
    def predict_proba(self, X):
        raise NotImplemented()


class LrModelCount(Model):
    def __init__(self, name='-', max_features=1000, analyzer='word', ngram_range=(1, 1), penalty='l2', C=1):
        super().__init__(name)
        self.vectorizer = CountVectorizer(max_features=max_features, analyzer=analyzer, ngram_range=ngram_range,
                                          min_df=100)
        self.model = lm.LogisticRegression(penalty=penalty, C=C, class_weight='balanced', fit_intercept=False)
        self._fitted = False
        
    def fit(self, X, y):
        X = self.vectorizer.fit_transform(X.text.values)
        self.model.fit(X, y)
        self._fitted = True
    
    def predict(self, X):
        if not self._fitted:
            raise Exception('Not fitted yet')
        X = self.vectorizer.transform(X.text.values)
        return self.model.predict(X)
    
    def predict_proba(self, X):
        if not self._fitted:
            raise Exception('Not fitted yet')
        X = self.vectorizer.transform(X.text.values)
        return self.model.predict_proba(X)


class LrModelTfidf(Model):
    def __init__(self, name='-', max_features=1000, penalty='l2', C=1):
        super().__init__(name)
        self.vectorizer = TfidfVectorizer(max_features=max_features, min_df=100)
        self.model = lm.LogisticRegression(penalty=penalty, C=C, class_weight='balanced', fit_intercept=False)
        self._fitted = False
        
    def fit(self, X, y):
        X = self.vectorizer.fit_transform(X.text.values)
        self.model.fit(X, y)
        self._fitted = True
    
    def predict(self, X):
        if not self._fitted:
            raise Exception('Not fitted yet')
        X = self.vectorizer.transform(X.text.values)
        return self.model.predict(X)

    def predict_proba(self, X):
        if not self._fitted:
            raise Exception('Not fitted yet')
        X = self.vectorizer.transform(X.text.values)
        return self.model.predict_proba(X)


class AverageModel():
    def __init__(self, models):
        self.models = models
        self._fitted = False
    
    def fit(self, X, y):
        for m in self.models:
            m.fit(X, y)
        self._fitted = True
    
    def predict(self, X):
        if not self._fitted:
            raise Exception('Not fitted yet')
        
        predictions = np.hstack([np.expand_dims(m.predict(X), -1) for m in self.models])
        predictions = (np.median(predictions, axis=1) > 0.5).astype(int)
        return predictions

    def predict_proba(self, X):
        if not self._fitted:
            raise Exception('Not fitted yet')
        
        predictions = []
        for model in self.models:
            prediction = model.predict_proba(X)
            if prediction.shape[1] > 1:
                prediction = prediction[:, 1]
            else:
                prediction = prediction.ravel()
            predictions.append(prediction)
                
        predictions = np.hstack([np.expand_dims(p, -1) for p in predictions])
        predictions = np.mean(predictions, axis=1)
        return predictions
    
    def save(self, filename):
        with open(filename, 'wb') as f:
            pickle.dump(self.models, f)

    def load(self, filename):
        with open(filename, 'rb') as f:
            self.models = pickle.load(f)
        self._fitted = True
