# Between the Lines of Tripadvisor Hotel Reviews
![Image from https://www.pexels.com/photo/bedroom-door-entrance-guest-room-271639/](https://github.com/chelseanbr/between-the-lines/blob/final_eda_modeling/images/hotel.jpg?raw=true)
#### Link to Presentation: 
https://docs.google.com/presentation/d/1l2uf6faNnBJOcEW3-zTkrklIsp8OO59qxc6GvtPD8bI/edit?usp=sharing
_____
## Context:
### Imagine you rent out properties like on Airbnb.
> How can you classify how people feel about your places to stay to reach out and improve reputation?
#### Solution: Mine hotel reviews “labeled” with ratings and use them to predict sentiment.

## Summary of Process
1. Web-scraped TripAdvisor hotel reviews
  * 2 EC2 instances ran in parallel over 2 days
  * Set up data cleaning, EDA, and modeling pipeline while scraping
2. Split data into 80:20 train/test, then split train into 80:20 train/validation
3. Balanced training data with undersampling
4. Evaluated models on accuracy and confusion matrix

## EDA
![countplot_reviews_byCity_full.png](https://github.com/chelseanbr/between-the-lines/blob/final_eda_modeling/images/countplot_reviews_byCity_full.png)

![boxplt_ratings_byCity_full.png](https://github.com/chelseanbr/between-the-lines/blob/final_eda_modeling/images/boxplt_ratings_byCity_full.png)

![countplot_ratings_full.png](https://github.com/chelseanbr/between-the-lines/blob/final_eda_modeling/images/countplot_ratings_full.png)

![pie_sentiments_full.png](https://github.com/chelseanbr/between-the-lines/blob/final_eda_modeling/images/pie_sentiments_full.png)

## Predictive Modeling

### Handling Imbalanced Classes
![pie_sentiments_train_undersample.png](https://github.com/chelseanbr/between-the-lines/blob/final_eda_modeling/images/pie_sentiments_train_undersample.png)

### NLP


## Conclusion


## Next Steps

