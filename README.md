# CommentsAnalysis

The main goal of this project - determine a graduation faculty of user by his comments in communities in social network.
A lot of machine learning and natural language processing technic are used. Dataset consist of 180k comments from 12k different users. Final solution consist of ensemble of the best models which predict class for each comment from certain user. Firstly, the class of each comment from user determined. After that, the class of user can be gotten by voting classifier.

- scripts.py - module for downloading data from social network (VK).
- EDA - notebook with exploration of data, cleaning  and preparing data for machine learning algorithms.
- DifferentModels - notebook with big amount of nlp models for predicting class of each comment. Different representation of comment: BOW, TfIdf(word and character level, ngrams), word2vec, LDA. Different models, from linear and XGBoost to LSTM. Also there is comparison with a human performance on this task.
- FinalSolution - best models and ensemble for final prediction.