import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import os
from graphviz import Source
from sklearn.tree import export_graphviz
from sklearn.preprocessing import OneHotEncoder
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.model_selection import cross_val_score


# File reading

def find_filenames(path_to_dir, suffix=None):
    filenames = os.listdir(path_to_dir)
    if suffix == None:
        return [filename for filename in filenames]
    else:
        return [filename for filename in filenames if filename.endswith(suffix)]


# Pandas df exploration functions

def get_nulls(df):
    # # print how many null values each column has, if any
    # print('Count of Null Values per Column, if any:\n\n{}'.format(df.isnull().sum()[df.isnull().sum() > 0]))
    # missing data
    total = df.isnull().sum().sort_values(ascending=False)
    percent = (df.isnull().sum()/df.isnull().count()).sort_values(ascending=False)
    missing_data = pd.concat([total, percent], axis=1, keys=['Total', 'Percent'])
    missing_data['Type'] = [df[col].dtype for col in missing_data.index]
    return missing_data

def print_unique_ct(df):
    # print how many unique values each column has
    print('Count of Unique Values per Column:\n')
    for col in df.columns:
        print('{}: {}'.format(col, len(df[col].unique())))

def get_cols_of_type(df, type):
    # print names of columns of given type
    cols = list(df.select_dtypes(type).columns)
    print('{} Columns ({}): \n{}'.format(type, len(cols), cols))
    return cols


# Plotting functions

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
