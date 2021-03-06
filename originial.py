import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from datetime import datetime
import os
import random
from keras.preprocessing import sequence
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
import tensorflow as tf
from keras.optimizers import Adam
from keras.models import load_model
from keras.callbacks import ModelCheckpoint
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score
from sklearn.metrics import precision_score
from sklearn.metrics import recall_score
from sklearn.metrics import f1_score
from sklearn.metrics import confusion_matrix
from keras.layers import Bidirectional
from keras.layers import Flatten
from keras.layers import TimeDistributed
from keras.layers.convolutional import Conv1D
from keras.layers.convolutional import MaxPooling1D
from keras.layers import ConvLSTM2D
from keras import backend as K


DepressionLevelsFile = "data/scores.csv"
dperessionLevelsData = pd.read_csv(DepressionLevelsFile)
dperessionLevelsData.head(5)

names = dperessionLevelsData['number'][:23]
MADRS1 = dperessionLevelsData['madrs1'][:23]
MADRS2 = dperessionLevelsData['madrs2'][:23]

MADRS_scores = []
for x in range(len(MADRS1)):
    avg_score = (int(MADRS1[x]) + int(MADRS2[x])) / 2
    if avg_score >= 7 and avg_score <= 19:
        MADRS_scores.append(0)
    if avg_score >= 20 and avg_score <= 34:
        MADRS_scores.append(1)


NameDepLevelMap = dict(zip(names, MADRS_scores))
print(NameDepLevelMap)


ConditionGroupFileNames = os.listdir('data/condition')


X = []
y = []

for fileName in ConditionGroupFileNames:
    df = pd.read_csv('data/condition/'+str(fileName))
    dates = df['date'].unique()
    activityLevelsPerDay = []
    for date in dates:
        if len(df[df['date']==date]) == 1440:
            temp = pd.DataFrame(df[df['date']==date]).drop(columns=['timestamp','date'])
            activityLevelsPerDay.append(temp)
    for dailyActivityLevel in activityLevelsPerDay:
        activityVector = np.array(dailyActivityLevel["activity"])
        if len(activityVector) == 1440:
            X.append(activityVector)
            y.append(NameDepLevelMap[str(fileName[:-4])])


combinedDict = list(zip(X, y))
random.shuffle(combinedDict)
X[:], y[:] = zip(*combinedDict)

X = np.array(X)
y = np.array(y)

X = np.reshape(X, (X.shape[0], 1, X.shape[1]))


def recall_m(y_true, y_pred):
    true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
    possible_positives = K.sum(K.round(K.clip(y_true, 0, 1)))
    recall = true_positives / (possible_positives + K.epsilon())
    return recall

def precision_m(y_true, y_pred):
    true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
    predicted_positives = K.sum(K.round(K.clip(y_pred, 0, 1)))
    precision = true_positives / (predicted_positives + K.epsilon())
    return precision

def f1_m(y_true, y_pred):
    precision = precision_m(y_true, y_pred)
    recall = recall_m(y_true, y_pred)
    return 2*((precision*recall)/(precision+recall+K.epsilon()))



seed = 7
kfold = StratifiedKFold(n_splits=10, shuffle=True, random_state=seed)


accuracy_scores = []
prec_scores = []
rec_scores = []
f1_scores = []

for train, test in kfold.split(X, y):
    model = Sequential()
    model.add(LSTM(64, input_shape=(1, 1440), return_sequences=True))
    model.add(LSTM(64, return_sequences=True))
    model.add(LSTM(64))
    model.add(Dense(1, activation='sigmoid'))

    adam = Adam(lr=0.001)
    model.compile(loss='binary_crossentropy', optimizer=adam, metrics=['accuracy', recall_m, precision_m, f1_m])

    model.fit(X[train], y[train], epochs=10, batch_size=128, verbose=0)
    scores = model.evaluate(X[test], y[test], verbose=0)

    print("%s: %.2f%%" % (model.metrics_names[1], scores[1] * 100))
    print("%s: %.2f%%" % (model.metrics_names[2], scores[2]))
    print("%s: %.2f%%" % (model.metrics_names[3], scores[3]))
    print("%s: %.2f%%" % (model.metrics_names[4], scores[4]))
    print("\n")
    accuracy_scores.append(scores[1] * 100)
    prec_scores.append(scores[2])
    rec_scores.append(scores[3])
    f1_scores.append(scores[4])


print('평균 AUC:', np.mean(accuracy_scores), '| 평균 오차범위:', np.std(accuracy_scores))
print('평균 pre:',np.mean(prec_scores), '| 평균 오차범위:', np.std(prec_scores))
print('평균 rec:',np.mean(rec_scores), '| 평균 오차범위:', np.std(rec_scores))
print('평균 f1:',np.mean(f1_scores), '| 평균 오차범위:', np.std(f1_scores))