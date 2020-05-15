# Between the Lines of Tripadvisor Hotel Reviews
![Image from https://www.pexels.com/photo/bedroom-door-entrance-guest-room-271639/](https://github.com/chelseanbr/between-the-lines/blob/final_eda_modeling/images/hotel.jpg?raw=true)
#### Link to Presentation: 
https://docs.google.com/presentation/d/1l2uf6faNnBJOcEW3-zTkrklIsp8OO59qxc6GvtPD8bI/edit?usp=sharing
_____
## Context
### Imagine you rent out properties like on Airbnb.
> How can you classify how people feel about your rentals in order to reach out and improve reputation?
#### Solution: Mine hotel reviews “labeled” with ratings and use them to predict sentiment.

## Summary of Process
![Tripadvisor_Logo_horizontal-lockup_registered_RGB.png](https://github.com/chelseanbr/between-the-lines/blob/final_eda_modeling/images/Tripadvisor_Logo_horizontal-lockup_registered_RGB.png) ![bs.png](https://github.com/chelseanbr/between-the-lines/blob/final_eda_modeling/images/bs.png)
1. Web-scraped TripAdvisor hotel reviews
  * 2 EC2 instances ran in parallel over 2 days
  * Set up data cleaning, EDA, and modeling pipeline while scraping
2. Split data into 80:20 train/test, then split train into 80:20 train/validation
3. Balanced training data with undersampling
4. Evaluated models on accuracy and confusion matrix

## EDA
* Whole dataset consisted of ~500,000 hotel reviews in English, 
each with a Tripadvisor “bubble” rating from 1 to 5

![countplot_reviews_byCity_full.png](https://github.com/chelseanbr/between-the-lines/blob/final_eda_modeling/images/countplot_reviews_byCity_full.png)

![boxplt_ratings_byCity_full.png](https://github.com/chelseanbr/between-the-lines/blob/final_eda_modeling/images/boxplt_ratings_byCity_full.png)

* Added sentiment label based on hotel rating per review

![countplot_ratings_full.png](https://github.com/chelseanbr/between-the-lines/blob/final_eda_modeling/images/countplot_ratings_full.png)

![pie_sentiments_full.png](https://github.com/chelseanbr/between-the-lines/blob/final_eda_modeling/images/pie_sentiments_full.png)

## Predictive Modeling

### Handling Imbalanced Classes
* Under-sampled train data to balance classes
* Train data qty reduced from ~300k to 94k observations
![pie_sentiments_train_undersample.png](https://github.com/chelseanbr/between-the-lines/blob/final_eda_modeling/images/pie_sentiments_train_undersample.png)
* Validation set had 77k observations, test set had 96k

### NLP
* Removed English 
stop words, digits, and 
punctuation

* Tried different stemmers/
lemmatizers and TF-IDF
max features

![mnb_accuracy_over_feature_size.png](https://github.com/chelseanbr/between-the-lines/blob/final_eda_modeling/images/mnb_accuracy_over_feature_size.png)

* Decided to proceed with 
TF-IDF, 
WordNetLemmatizer,
and 5,000 features

## Results
![confusion_matrix_final_lr_test.png](https://github.com/chelseanbr/between-the-lines/blob/final_eda_modeling/images/confusion_matrix_final_lr_test.png)

![wordcloud_positive.png](https://github.com/chelseanbr/between-the-lines/blob/final_eda_modeling/images/wordcloud_positive.png)

![wordcloud_neutral.png](https://github.com/chelseanbr/between-the-lines/blob/final_eda_modeling/images/wordcloud_neutral.png)

![wordcloud_negative.png](https://github.com/chelseanbr/between-the-lines/blob/final_eda_modeling/images/wordcloud_negative.png)

## Next Steps
* Try out model on other data like tweets in the context of hotels/places to stay
* Explore advanced NLP/ML methods like Word2Vec, LSTM recurrent neural networks
* Mine more data and build a hotel recommender system
