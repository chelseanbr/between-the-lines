import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

from graphviz import Source
from sklearn.tree import export_graphviz
from sklearn.preprocessing import OneHotEncoder
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.model_selection import cross_val_score

from nltk.corpus import stopwords
from nltk.tokenize import RegexpTokenizer
from nltk.stem.porter import PorterStemmer
from nltk.stem.snowball import SnowballStemmer
from nltk.stem.wordnet import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer


# File reading

def merge_csv_mult_dir(path_to_dir):
    # Get all folders in dir
    folders = os.listdir(path_to_dir)
    print('Folders:', folders)
    # From each folder, read all CSV files
    dfs = []
    for folder in folders:
    #     print(folder)
        data_dir = path_to_dir + '/' + folder + '/'
        csv_filenames = os.listdir(data_dir)    
        for name in csv_filenames:
            df = pd.read_csv(data_dir + name)
            df['csv'] = name
            df['folder'] = folder
            dfs.append(df)
    df_all = pd.concat(dfs, ignore_index=True)
    return df_all


# Pandas df exploration

def get_nulls(df):
    # Get count, pct, and type of missing data (per column)
    total = df.isnull().sum().sort_values(ascending=False)
    percent = (df.isnull().sum()/df.isnull().count()).sort_values(ascending=False)
    missing_data = pd.concat([total, percent], axis=1, keys=['Total', 'Percent'])
    missing_data['Type'] = [df[col].dtype for col in missing_data.index]
    return missing_data

def print_unique_ct(df):
    # Print how many unique values each column has
    print('Count of Unique Values per Column:\n')
    for col in df.columns:
        print('{}: {}'.format(col, len(df[col].unique())))

def get_cols_of_type(df, type):
    # Print names of columns of given type
    cols = list(df.select_dtypes(type).columns)
    print('{} Columns ({}): \n{}'.format(type, len(cols), cols))
    return cols


# Cleaning & preparing data

def clean_and_prep(df):
    # # Change 'review_date' to datetime type
    # df['review_date'] = pd.to_datetime(df['review_date'])

    # Drop duplicate rows
    df.drop_duplicates(inplace=True)
    # Fill nulls for 'user_location' with 'n/a'
    df.fillna({'user_location': 'n/a'}, inplace=True)

    # # Add col 'review_length' from 'review_body'
    # df['review_length'] = df['review_body'].str.len()

    # Get 'City' from 'folder'
    df[['City', 'drop']] = df['folder'].str.split('-', 1, expand=True)
    df.drop(columns=['drop'], inplace=True)
    # Add 'sentiment' column mapped by 'rating'
    df['sentiment'] = df['rating'].map({1: 'negative', 2: 'negative', 3: 'neutral', 4:'positive', 5:'positive'})
    # Add 'sentiment' column mapped by 'sentiment'
    df['polarity'] = df['sentiment'].map({'negative': 0, 'neutral': 0.5, 'positive': 1})
    # Add 'sentiment_int' column mapped by 'sentiment'
    df['sentiment_int'] = (df['polarity'] * 2).astype(int)
    # Move 'sentiment' col to be last
    last_col = df.pop('sentiment')
    df.insert(df.shape[1], 'sentiment', last_col)
    return df


# Plotting

def plot_hist(df, var, fig, ax):
    # histogram of var
    sns.distplot(df[var], ax=ax)
    # skewness and kurtosis
    print('Skewness: {:.4f}'.format(df[var].skew()))
    print('Kurtosis: {:.4f}'.format(df[var].kurt()))
    return fig, ax

def plot_scatter(df, var, target, ylim=(0,800000)):
    # scatterplot of var/target
    data = pd.concat([df[target], df[var]], axis=1)
    data.plot.scatter(x=var, y=target, ylim=ylim, color='b')

def plot_boxplot(df, var, target, figsize=(8, 6), ylim=(0,800000)):
    # boxplot of var/target
    data = pd.concat([df[target], df[var]], axis=1)
    fig, ax = plt.subplots(figsize=figsize)
    fig = sns.boxplot(x=var, y=target, data=data)
    fig.axis(ymin=ylim[0], ymax=ylim[1])

def plot_corr(df, figsize=(12, 9), vmax=.8):
    # corr matrix of df
    corrmat = df.corr()
    fig, ax = plt.subplots(figsize=figsize)
    sns.heatmap(corrmat, vmax=vmax, square=True, xticklabels=True, yticklabels=True)

def plot_target_corr(df, target, num_vars=5, figsize=(12, 9)):
    # target correlation matrix
    corrmat = df.corr()
    cols = corrmat.nlargest(num_vars, target)[target].index
    cm = np.corrcoef(df[cols].values.T)
    sns.set(font_scale=1.25)
    fig, ax = plt.subplots(figsize=figsize)
    ax = sns.heatmap(cm, cbar=True, annot=True, square=True, fmt='.2f', annot_kws={'size': 12}, 
                     yticklabels=cols.values, xticklabels=cols.values)
    bottom, top = ax.get_ylim()
    ax.set_ylim(bottom + 0.5, top - 0.5)
    fig.tight_layout()

def plot_scattermatrix(df, cols, height=2.5):
    # scatter matrix
    sns.set()
    sns.pairplot(df[cols], height = height)

def plot_pie(series, fig, ax):
    # fig, ax = plt.subplots(figsize=(8,8))

    series.value_counts().plot.pie(ax=ax, autopct='%1.2f%%')

    plt.rcParams['font.size'] = 18
    
    fig.tight_layout()
    return fig, ax

def plot_counts_bygroup(df, features, groupby, fig, axs):
    # fig, axs = plt.subplots(6, 4, figsize=(14,18))

    for feature, ax in zip(features, axs.flatten()[:len(features)]):
        ax = sns.countplot(data=df, x=feature, hue=groupby, ax=ax, order=df[feature].value_counts().index)
        ax.legend_.remove()

    fig.tight_layout()
    return fig, axs

def plot_topN_features(feature_importances, feature_list, N):
    # Plot the feature importance
    idxes = np.argsort(-feature_importances)
    feature_list[idxes]
    rev_sort_feature_importances = feature_importances[idxes]
    rev_sort_feature_cols = feature_list[idxes]

    feat_scores = pd.DataFrame({'Fraction of Samples Affected' : rev_sort_feature_importances[:N]},
                               index=rev_sort_feature_cols[:N])
    feat_scores = feat_scores.sort_values(by='Fraction of Samples Affected')
    feat_scores.plot(kind='barh')
    
    plt.title('Feature Importances', size=25)
    plt.ylabel('Features', size=25)
    return plt, rev_sort_feature_cols

def plot_tree(tree, feature_list, out_file=None):
    # Source(plot_tree(tree, feature_list, out_file=None)) to print in Jupyter nb
    return export_graphviz(tree, out_file=out_file, feature_names=feature_list)


# Modeling

def fit_pred_score_Nfold(model, X_train, y_train, N=10, model_name=None, scoring='accuracy'):
    # Fit model
    model.fit(X_train, y_train)
    # Get N-fold Cross-Validation score
    if model_name is None:
        model_name=model.__class__.__name__
    score = np.mean(cross_val_score(model, X_train, y_train, scoring=scoring, cv=N))
    print(model_name + ' {}, {}-fold CV on Train Data: {:0.3f}'.format(scoring, N, score))


# NLP
def build_text_vectorizer(contents, use_tfidf=True, use_stemmer=False, max_features=None):
    '''
    Build and return a **callable** for transforming text documents to vectors,
    as well as a vocabulary to map document-vector indices to words from the
    corpus. The vectorizer will be trained from the text documents in the
    `contents` argument. If `use_tfidf` is True, then the vectorizer will use
    the Tf-Idf algorithm, otherwise a Bag-of-Words vectorizer will be used.
    The text will be tokenized by words, and each word will be stemmed iff
    `use_stemmer` is True. If `max_features` is not None, then the vocabulary
    will be limited to the `max_features` most common words in the corpus.
    '''
    Vectorizer = TfidfVectorizer if use_tfidf else CountVectorizer
#     tokenizer = RegexpTokenizer(r"[\w']+")
    tokenizer = RegexpTokenizer(r"[a-zA-Z]+")
#     stem = PorterStemmer().stem if use_stemmer else (lambda x: x)
    if use_stemmer=='porter':  
        stem = PorterStemmer().stem
        print('Using PorterStemmer')
    elif use_stemmer=='snowball':    
        stem = SnowballStemmer('english').stem
        print('Using SnowballStemmer')
    elif use_stemmer=='lem':    
        stem = WordNetLemmatizer().lemmatize
        print('Using WordNetLemmatizer')
    else: 
        stem = (lambda x: x)
        print('No Stemmer')

    stop_set = set(stopwords.words('english'))

    # Closure over the tokenizer et al.
    def tokenize(text):
        tokens = tokenizer.tokenize(text)
        stems = [stem(token) for token in tokens if token not in stop_set]
        return stems

    vectorizer_model = Vectorizer(strip_accents='unicode', lowercase=True, 
                                  tokenizer=tokenize, max_features=max_features)
    vectorizer_model.fit(contents)
    vocabulary = np.array(vectorizer_model.get_feature_names())

    # Closure over the vectorizer_model's transform method.
    def vectorizer(X):
        return vectorizer_model.transform(X).toarray()

    return vectorizer, vocabulary