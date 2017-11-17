# CommentsAnalysis

The main goal of this project is determine a graduation faculty of the user by his comments in communities in social networks.
A lot of machine learning and natural language processing techniques are used. The dataset consists of 180k comments from 12k different users. Final solution represents an ensemble of the best models which predict class of each comment from the user. Firstly, the class of each comment from the user determined. After that, the class of the user can be obtained by voting classifier.

- scripts.py - module for downloading data from social networks (VK).
- EDA - notebook with exploration of data, cleaning  and preparing data for machine learning algorithms.
- DifferentModels - notebook with a big amount of nlp models for predicting class of each comment. Different representations of comments: BOW, TfIdf(word and character level, ngrams), word2vec, LDA. Different models, from linear and XGBoost to LSTM. Also there is comparison with a human performance on this task.
- FinalSolution - best models and ensembles for final prediction.