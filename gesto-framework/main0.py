print("GESTO-V1 dataset research paper.")
print("\tThis is the program that tests different feature extraction techniques")
print("\ton the dataset.")

print("\nImporting the necesary dependencies")

print("\n\tImporting configuration file");import config as cfg

print("\n\tImporting time");import time
print("\n\tImporting itertools");import itertools

print("\n\tImporting numpy");import numpy as np
print("\n\tImporting pandas");import pandas as pd
print("\n\tImporting matplotlib.pyplot");import matplotlib.pyplot as plt

print("\n\tImporting opencv");import cv2

print("\n\tImporting tqdm");from tqdm import tqdm
print("\n\tImporting glob");from glob import glob
print("\n\tImporting re");import re
print("\n\tImporting random");import random as random
print("\n\tImporting PCA");from sklearn.decomposition import PCA,IncrementalPCA
print("\n\tImporting LDA");from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
print("\n\tImporting SciPy stats");from scipy import stats



print("\n\tDone importing\n")

class Dataset(object):
    def __init__(self,location,verbose=False):
        self.verbose = True
        self.database_grouped = None
        self.database = pd.DataFrame(columns=["filepath","subject","class","id"])

        self.train = pd.DataFrame(columns=["filepath","subject","class","id"])
        self.test = pd.DataFrame(columns=["filepath","subject","class","id"])
        self.val = pd.DataFrame(columns=["filepath","subject","class","id"])

        self.subjects = None
        self.n_subjects = 0
        self.discover_data(location)
        self.save()

    def discover_data(self,location):
        if self.verbose:print("Loading and compiling REGEX")

        regex_str, group = cfg.DATASET_REGEX
        if self.verbose:print(f'\tREGEX string: "{regex_str}"')
        regex = re.compile(regex_str)

        if self.verbose:print("Exploring the data tree")

        new_entries = []
        for filepath in self.get_filepaths():
            info = regex.search(filepath)
            if info is not None:
                entry = {"filepath":filepath,"subject":info[group['subject']],"class":info[group['class']],"id":info[group['id']]}
                new_entries.append(entry)

        self.database  = self.database.append(new_entries)
        self.database_grouped = self.database.set_index('subject').groupby("subject")
        self.subjects = [self.database_grouped.get_group(str(i)) for i in range(len(self.database_grouped)) ]
        self.n_subjects = len(self.subjects)

    def get_filepaths(self):
            if self.verbose:
                print("\nGetting the filepaths")
                iteror = tqdm(glob(cfg.DATASET_LOCATION + "*/*/*.png"))

                return iteror
            return glob(cfg.DATASET_LOCATION + "*/*/*.png")

    def save(self):
        self.database.to_csv("dataset.csv")

    def split(self,train=0.8,test = 0.2,val = 0,seed=12334):
        total = train+test+val

        train /= total
        test /= total
        val /= total

        np.random.seed(seed)
        random_subjects = np.random.random(self.n_subjects)

        train_index = random_subjects <= train
        test_index = (random_subjects > train) & (random_subjects <= train+test)
        val_index = random_subjects > train+test

        self.train = [self.subjects[i] for i in range(self.n_subjects) if train_index[i]]
        self.test  = [self.subjects[i] for i in range(self.n_subjects) if test_index[i] ]
        self.val   = [self.subjects[i] for i in range(self.n_subjects) if val_index[i]  ]

        if self.verbose:
            print(f"\nSplitting into train ({train*100}%) and test ({test*100}%) sets:")

            print(f"\t{len(self.train)} subjects in train set, {100*len(self.train)/self.n_subjects}%")
            print(f"\t{len(self.test)} subjects in test set, {100*len(self.test)/self.n_subjects}%")
            print(f"\t{len(self.val)} subjects in validation set, {100*len(self.val)/self.n_subjects}%")

    def load(self,which="train"):
        set_to_load = None

        if which == "train":
            set_to_load = self.train
        elif which == "test":
            set_to_load = self.test
        elif which == "val":
            set_to_load = self.val

        print(f"\n\tLoading {which} set")

        targets = np.array([])
        features = []

        iteror = tqdm(set_to_load)

        for subject in iteror:
            targets = np.append(targets,subject["class"])
            subject_pictures = []
            for filepath in subject["filepath"]:
                img = cv2.imread(filepath, cv2.IMREAD_GRAYSCALE).ravel()
                features.append(img)

        print(f"\n\t\t{len(features)} images in the feature vector")
        print(f"\n\t\t{len(targets)} classes in the target vector")

        return np.vstack(features),targets

class Model():
    def __init__(self,kind,labels):
        self.kind = kind
        self.labels = labels
        self.y_train = []
    def transform(self,data):
        if self.kind == None:
            return data
    def predict(self,data):
        if self.kind == None:
            output = random.choices(self.y_train,k=data.shape[0])
            return np.array(output)


def standardize_data(data,verbose=True,method = "zscore"):
    if method == "zscore":return stats.zscore(data,axis=1,ddof=1)

def extract_features(traindata,testdata,method=None,parameters=None,standardize=True,verbose=True):
    if standardize:
        if verbose:print("\t\tStandardizing data (zscore)")
        trainout = standardize_data(traindata,verbose)
        testout = standardize_data(testdata,verbose)

    if method == None: # Just flattening
        if verbose:print("\t\tNot applying any feature extraction method")


    elif method == "PCA":
        model = PCA(**parameters)
        if verbose:print("\t\tFitting PCA model")

        trainout = model.fit_transform(traindata)
        testout = model.transform(testdata)


    elif method == "IncrementalPCA":
        batch_size = parameters["n_components"]
        batches = int(traindata.shape[0]/batch_size)

        if verbose:
            print("\t\tFitting IncrementalPCA batches")
            iteror = tqdm(range(batches))

        model = IncrementalPCA()

        for batch in iteror:
            model.partial_fit(traindata[batch*batch_size:(batch+1)*batch_size])

        if verbose:print("\t\tApplying IncrementalPCA tranformation to the batches")

        trainout = model.transform(traindata)
        testout = model.transform(testdata)

    return [trainout,testout]

def train_classifier(data,targets,labels,method=None,parameters=None,verbose=True):

    if method == None:
        if verbose:print("\t\tRandom guessing method")
        classifier = Model(None,labels)
        classifier.y_train = targets

    if method == "LDA":
        classifier = LinearDiscriminantAnalysis()
        classifier.fit(data,targets)
    return classifier

import sklearn.metrics as skm

def get_metrics(y_true,y_pred,labels):
    metrics = {}

    metrics['confusion_matrix'] = skm.confusion_matrix(y_true, y_pred,labels=labels)
    metrics['accuracy'] = skm.accuracy_score(y_true,y_pred)
    metrics['recall'] = skm.recall_score(y_true, y_pred,labels=labels,average='weighted')
    metrics['precision'] = skm.precision_score(y_true, y_pred,labels=labels,average='weighted')

    return metrics

def plot_confusion_matrix(cm,
                          target_names,
                          title='Confusion matrix',
                          cmap=None,
                          normalize=True):
    """
    given a sklearn confusion matrix (cm), make a nice plot

    Arguments
    ---------
    cm:           confusion matrix from sklearn.metrics.confusion_matrix

    target_names: given classification classes such as [0, 1, 2]
                  the class names, for example: ['high', 'medium', 'low']

    title:        the text to display at the top of the matrix

    cmap:         the gradient of the values displayed from matplotlib.pyplot.cm
                  see http://matplotlib.org/examples/color/colormaps_reference.html
                  plt.get_cmap('jet') or plt.cm.Blues

    normalize:    If False, plot the raw numbers
                  If True, plot the proportions

    Usage
    -----
    plot_confusion_matrix(cm           = cm,                  # confusion matrix created by
                                                              # sklearn.metrics.confusion_matrix
                          normalize    = True,                # show proportions
                          target_names = y_labels_vals,       # list of names of the classes
                          title        = best_estimator_name) # title of graph

    Citiation
    ---------
    http://scikit-learn.org/stable/auto_examples/model_selection/plot_confusion_matrix.html

    """

    accuracy = np.trace(cm) / np.sum(cm).astype('float')
    misclass = 1 - accuracy

    if cmap is None:
        cmap = plt.get_cmap('Blues')

    plt.figure(figsize=(8, 6))
    plt.imshow(cm, interpolation='nearest', cmap=cmap)
    plt.title(title)
    plt.colorbar()

    if target_names is not None:
        tick_marks = np.arange(len(target_names))
        plt.xticks(tick_marks, target_names, rotation=45)
        plt.yticks(tick_marks, target_names)

    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]


    thresh = cm.max() / 1.5 if normalize else cm.max() / 2
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        if normalize:
            plt.text(j, i, "{:0.4f}".format(cm[i, j]),
                     horizontalalignment="center",
                     color="white" if cm[i, j] > thresh else "black")
        else:
            plt.text(j, i, "{:,}".format(cm[i, j]),
                     horizontalalignment="center",
                     color="white" if cm[i, j] > thresh else "black")


    plt.tight_layout()
    plt.ylabel('True label')
    plt.xlabel('Predicted label\naccuracy={:0.4f}; misclass={:0.4f}'.format(accuracy, misclass))


#Things done
# Histogram is equalized

#Things to do
# Either PCA - LDA - WVTF

gesto_v1 = Dataset(cfg.DATASET_LOCATION,verbose=True)

metrics = {
            }



for e, task in enumerate(cfg.TASKS):
    print(f"\nTask {e} of {len(cfg.TASKS)}:\n\tTask name: {task['name']}\n\t\t{task['description']}\n")
    time.sleep(5)
    task_metrics = []

    for i in range(task['iterations']):
        gesto_v1.split(0.8,0.2,seed=198762)
        print("\n\tLoading train and test sets")

        train , y_train = gesto_v1.load('train')
        print(f"\n\t\tTrain matrix shape {train.shape}")

        test, y_test = gesto_v1.load('test')
        print(f"\n\t\tTest matrix shape {test.shape}")
        labels = list(set(y_train))


        print("\n\tFeature extraction of train and test set:")
        x_train, x_test = extract_features(train,test,**task['feature_extraction'])
        print(f"\n\t\tReduced train matrix shape {x_train.shape}")
        print(f"\n\t\tReduced test matrix shape {x_test.shape}")
        print(f"\n\t\tTotal reduction: {train.shape[1]/x_train.shape[1]}")

        print("\n\tTraining model:")
        model = train_classifier(x_train,y_train,labels,**task['classification'])
        print("\n\t\tTrained model successfully")

        print("\n\tDoing predictions on the test set")
        y_test_predicted = model.predict(x_test)
        print("\n\t\tPredictions made successfully")

        print("\n\tMeasuring and saving task iteration metrics")
        iter_metrics = get_metrics(y_test_predicted,y_test,labels)

        task_metrics.append(iter_metrics)

        plot_confusion_matrix(iter_metrics['confusion_matrix'],labels,
                                title=f"Confusion matrix of task: {task['name']}, iteration {i}")

        print("\n\t\tMetrics done successfully")
    time.sleep(2)
    metrics.update([[task['name'],[task_metrics]]])

plt.show()
