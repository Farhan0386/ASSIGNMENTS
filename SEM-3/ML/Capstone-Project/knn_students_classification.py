import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report

# 1. Generate Self-Contained Synthetic Student Dataset (CGPA and IQ)
np.random.seed(42)
n_samples = 300

# Generate CGPA (range 2.0 to 4.0) and IQ (range 80 to 140)
cgpa = np.random.uniform(2.0, 4.0, n_samples)
iq = np.random.normal(105, 12, n_samples).clip(80, 140)

# Define a rule/boundary for academic performance classification (e.g., Honor roll / High achiever = 1, Regular = 0)
# Students with CGPA >= 3.3 or (CGPA >= 3.0 and IQ >= 110) tend to be class 1
performance = np.where((cgpa >= 3.3) | ((cgpa >= 3.0) & (iq >= 110)), 1, 0)
# Add a little noise/overlap
noise_idx = np.random.choice(n_samples, size=15, replace=False)
performance[noise_idx] = 1 - performance[noise_idx]

df = pd.DataFrame({
    'CGPA': cgpa,
    'IQ': iq,
    'Performance': performance
})

print("--- Student Dataset Overview ---")
print(f"Total Samples: {len(df)}")
print(f"Class Distribution:\n{df['Performance'].value_counts().to_dict()}")
print("\nSample Data:")
print(df.head())

# 2. Features and Target Split
X = df[['CGPA', 'IQ']]
y = df['Performance']

# 3. Train-Test Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

# 4. Feature Scaling (Crucial for K-NN since CGPA and IQ have vastly different scales)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# 5. Find Suitable K using validation accuracy test
k_values = range(1, 20)
accuracies = []

for k in k_values:
    knn = KNeighborsClassifier(n_neighbors=k)
    knn.fit(X_train_scaled, y_train)
    y_pred_val = knn.predict(X_test_scaled)
    accuracies.append(accuracy_score(y_test, y_pred_val))

best_k = k_values[np.argmax(accuracies)]
print(f"\nTested K values [1-19]. Optimal K selected: {best_k} (Accuracy: {max(accuracies)*100:.2f}%)")

# Plot K vs Accuracy and save
plt.figure(figsize=(8, 5))
plt.plot(k_values, accuracies, marker='o', linestyle='-', color='b')
plt.title('K-NN: K Value vs Accuracy')
plt.xlabel('Value of K')
plt.ylabel('Accuracy')
plt.grid(True)
plt.savefig('knn_k_vs_accuracy.png')
plt.close()
print("Saved K vs Accuracy plot as knn_k_vs_accuracy.png")

# 6. Train Final K-NN Model with Optimal K
final_knn = KNeighborsClassifier(n_neighbors=best_k)
final_knn.fit(X_train_scaled, y_train)

y_pred = final_knn.predict(X_test_scaled)
acc = accuracy_score(y_test, y_pred)
cm = confusion_matrix(y_test, y_pred)

print(f"\n--- Final Model Evaluation (K={best_k}) ---")
print(f"Accuracy: {acc * 100:.2f}%")
print("\nConfusion Matrix:")
print(cm)

print("\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=['Regular (0)', 'High Achiever (1)']))

# 7. Test on Custom Student Profiles (using DataFrame to preserve feature names for StandardScaler)
custom_students = pd.DataFrame([
    [3.7, 125], # High CGPA, High IQ -> Expected High Achiever
    [2.4, 90],  # Low CGPA, Low IQ -> Expected Regular
    [3.2, 115]  # Moderate CGPA, High IQ
], columns=['CGPA', 'IQ'])
custom_scaled = scaler.transform(custom_students)
custom_preds = final_knn.predict(custom_scaled)

print("--- Custom Student Predictions ---")
for i, (_, student) in enumerate(custom_students.iterrows()):
    pred = custom_preds[i]
    status = "High Achiever (1)" if pred == 1 else "Regular (0)"
    print(f"Student {i+1} [CGPA: {student['CGPA']}, IQ: {student['IQ']}] --> Predicted Classification: {status}")

print("\nK-NN student classification completed successfully!")
