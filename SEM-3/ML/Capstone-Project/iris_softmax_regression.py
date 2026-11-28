import numpy as np
import pandas as pd
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

# 1. Load Iris Dataset (built-in scikit-learn dataset, self-contained)
iris = load_iris()
X = iris.data
y = iris.target
target_names = iris.target_names

df = pd.DataFrame(X, columns=iris.feature_names)
df['species'] = y

print("--- Iris Dataset Overview ---")
print(f"Total Samples: {len(df)}")
print(f"Classes: {target_names.tolist()}")
print("\nSample Data:")
print(df.head())
print("\nClass Distribution:")
print(pd.Series(y).value_counts().sort_index())

# 2. Train-Test Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# 3. Feature Scaling (Important for regularized Softmax Regression / Logistic Regression)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# 4. Softmax Regression (Logistic Regression with multi_class='multinomial')
# In newer sklearn versions, multi_class defaults to 'auto' which uses 'multinomial' for multi-class
model = LogisticRegression(solver='lbfgs', max_iter=200, random_state=42)
model.fit(X_train_scaled, y_train)

# 5. Evaluation
y_pred = model.predict(X_test_scaled)
acc = accuracy_score(y_test, y_pred)
cm = confusion_matrix(y_test, y_pred)

print("\n--- Model Evaluation ---")
print(f"Accuracy: {acc * 100:.2f}%")
print("\nConfusion Matrix:")
print(cm)

print("\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=target_names))

# 6. Test on custom sample flower measurements
sample_flowers = np.array([
    [5.1, 3.5, 1.4, 0.2], # Expected: setosa
    [6.7, 3.0, 5.2, 2.3], # Expected: virginica
    [5.9, 2.8, 4.8, 1.8]  # Expected: versicolor or virginica
])
sample_scaled = scaler.transform(sample_flowers)
sample_preds = model.predict(sample_scaled)
sample_probs = model.predict_proba(sample_scaled)

print("--- Custom Flower Predictions ---")
for i, (flower, pred, prob) in enumerate(zip(sample_flowers, sample_preds, sample_probs)):
    class_name = target_names[pred]
    max_prob = np.max(prob) * 100
    print(f"Sample {i+1} Measurements {flower.tolist()} --> Predicted Species: {class_name} (Confidence: {max_prob:.2f}%)")

print("\nIris softmax regression completed successfully!")