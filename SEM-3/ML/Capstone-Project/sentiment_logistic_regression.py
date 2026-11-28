import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report

# 1. Self-contained synthetic review dataset (larger for better learning)
positive_reviews = [
    "This product is amazing! I love it so much.",
    "Excellent quality, highly recommend to everyone.",
    "Great customer service and fast delivery.",
    "Best purchase I have made this year! Super happy.",
    "Really good performance and top notch design.",
    "Fantastic experience! Will buy again for sure.",
    "Works perfectly, very satisfied with this item.",
    "Awesome features and very easy to use.",
    "Loved the packaging and overall build quality.",
    "Five stars! Exceeded my expectations.",
    "Decent value for money, satisfied overall.",
    "Impressive speed and reliable functionality.",
    "Wonderful experience, super friendly user interface.",
    "Highly impressive product, works like a charm.",
    "Very nice! Exactly what I was looking for.",
    "Perfect quality, could not ask for anything better.",
    "Outstanding performance, worth every penny.",
    "Super happy with my purchase, highly recommended.",
    "Excellent build quality, very durable and strong.",
    "Amazing value, great product for the price.",
    "Fantastic product, everything works flawlessly.",
    "Very pleased with this item, excellent choice.",
    "Top quality product, exceeds expectations easily.",
    "Great product, fast shipping and well packaged.",
    "Love this product, works perfectly as described.",
    "Excellent buy, great quality and fast delivery.",
    "Superb quality, exactly what I needed and wanted.",
    "Perfect! No complaints at all, highly satisfied.",
    "Wonderful quality, very happy with this purchase.",
    "Excellent product, will definitely buy again soon."
]

negative_reviews = [
    "Terrible product, broke down on the first day.",
    "Completely disappointed. Waste of money.",
    "Horrible quality, do not buy this item.",
    "Very slow performance and poor customer support.",
    "Item arrived damaged and unusable.",
    "Bad experience, failed to meet any expectation.",
    "Worst purchase ever! Extremely frustrating.",
    "Defective item, returned it immediately.",
    "Useless product, does not work as advertised.",
    "Cheap materials, broke easily within a week.",
    "Poor design and very hard to setup.",
    "Regret buying this, zero customer service.",
    "Not good at all, total failure.",
    "Very unsatisfied, bad build quality and slow.",
    "Extremely disappointed with this garbage product.",
    "Absolutely terrible, do not waste your money.",
    "Completely broken out of the box, useless.",
    "Poor quality control, item defective on arrival.",
    "Waste of money, stopped working after one day.",
    "Horrible experience, product is completely flawed.",
    "Bad construction, pieces missing and broken.",
    "Extremely poor quality, feels very cheaply made.",
    "Terrible customer service, refused to help me.",
    "Useless and broken, complete disappointment.",
    "Very poor design, difficult to use and unreliable.",
    "Complete garbage, save your money and avoid.",
    "Disappointing product, nothing works as intended.",
    "Low quality materials, broke within hours of use.",
    "Awful experience, product arrived broken and useless.",
    "Terrible value, overpriced for such poor quality."
]

reviews = positive_reviews + negative_reviews
sentiments = [1] * len(positive_reviews) + [0] * len(negative_reviews)

df = pd.DataFrame({'review_text': reviews, 'sentiment': sentiments})
print("--- Sentiment Dataset Overview ---")
print(f"Total Samples: {len(df)}")
print(f"Positive Count: {sum(df['sentiment'] == 1)}")
print(f"Negative Count: {sum(df['sentiment'] == 0)}")
print("\nSample Data:")
print(df.head())

# 2. Train-Test Split
X = df['review_text']
y = df['sentiment']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# 3. Vectorization (TF-IDF)
vectorizer = TfidfVectorizer(lowercase=True, stop_words='english', max_features=500)
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

# 4. Logistic Regression Model Training
model = LogisticRegression(random_state=42, max_iter=1000)
model.fit(X_train_vec, y_train)

# 5. Evaluation
y_pred = model.predict(X_test_vec)
acc = accuracy_score(y_test, y_pred)
cm = confusion_matrix(y_test, y_pred)

print("\n--- Model Evaluation ---")
print(f"Accuracy: {acc * 100:.2f}%")
print("\nConfusion Matrix:")
print("                 Predicted Neg  Predicted Pos")
print(f"Actual Negative     {cm[0][0]:<12} {cm[0][1]:<12}")
print(f"Actual Positive     {cm[1][0]:<12} {cm[1][1]:<12}")

print("\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=['Negative', 'Positive']))

# 6. Test on new unseen custom reviews
sample_unseen = [
    "This is the best gadget ever, totally worth it!",
    "Awful product, broke in two minutes and stopped working.",
    "Excellent quality and great customer service!",
    "Horrible experience, completely waste of money.",
    "Really good value for the price, recommended."
]
sample_vec = vectorizer.transform(sample_unseen)
sample_preds = model.predict(sample_vec)

print("--- Custom Text Predictions ---")
for text, pred in zip(sample_unseen, sample_preds):
    label = "Positive" if pred == 1 else "Negative"
    print(f"Review: \"{text}\" --> Predicted Sentiment: {label}")

print("\nSentiment logistic regression completed successfully!")