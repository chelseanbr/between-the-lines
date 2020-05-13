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

def fit_pred_score_Nfold(model, X_train, y_train, X_test, test_idx, target_col, N=10, model_name=None, csv=None):
    # Fit model
    model.fit(X_train, y_train)
    # Predict
    y_pred = model.predict(X_test)
    # Create submission if csv arg passed
    if csv is not None:
        y_pred_df = pd.DataFrame(y_pred, index=test_idx, columns=[target_col])
        y_pred_df.head()
        y_pred_df.to_csv('submissions/' + csv + '.csv')
    # Get N-fold Cross-Validation RMSE score
    if model_name is None:
        model_name=model.__class__.__name__
    rmse = np.mean(np.sqrt(-cross_val_score(model, X_train, y_train, scoring='neg_mean_squared_log_error', cv=N)))
    print(model_name + ' RMSLE, {}-fold CV on Train Data: {:0.3f}'.format(N, rmse))