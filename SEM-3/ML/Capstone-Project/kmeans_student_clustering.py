import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

# 1. Generate Self-Contained Synthetic Student Dataset (CGPA and IQ)
np.random.seed(42)
n_samples = 300

# Create 3 distinct natural student groups:
# Group 1: Average students
cgpa_g1 = np.random.normal(2.7, 0.2, 100).clip(2.0, 4.0)
iq_g1 = np.random.normal(100, 8, 100).clip(80, 140)

# Group 2: High Achievers (High CGPA, High IQ)
cgpa_g2 = np.random.normal(3.6, 0.2, 100).clip(2.0, 4.0)
iq_g2 = np.random.normal(122, 8, 100).clip(80, 140)

# Group 3: Hardworking / High IQ lower GPA or vice versa (e.g. Underachievers / Brilliant slackers)
cgpa_g3 = np.random.normal(3.1, 0.25, 100).clip(2.0, 4.0)
iq_g3 = np.random.normal(110, 10, 100).clip(80, 140)

cgpa = np.concatenate([cgpa_g1, cgpa_g2, cgpa_g3])
iq = np.concatenate([iq_g1, iq_g2, iq_g3])

df = pd.DataFrame({
    'CGPA': cgpa,
    'IQ': iq
})

print("--- Student Clustering Dataset Overview ---")
print(f"Total Students: {len(df)}")
print(df.head())

# 2. Feature Scaling (Essential for K-Means distance calculations)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(df[['CGPA', 'IQ']])

# 3. Elbow Method to determine optimal K
inertia = []
k_range = range(1, 10)

for k in k_range:
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    kmeans.fit(X_scaled)
    inertia.append(kmeans.inertia_)

# Plot Elbow Curve and save
plt.figure(figsize=(8, 5))
plt.plot(k_range, inertia, marker='o', linestyle='-', color='r')
plt.title('Elbow Method for Optimal K')
plt.xlabel('Number of Clusters (K)')
plt.ylabel('Inertia (Sum of Squared Distances)')
plt.grid(True)
plt.savefig('kmeans_elbow_curve.png')
plt.close()
print("\nElbow curve saved as kmeans_elbow_curve.png")

# 4. Apply K-Means with Optimal K (K=3 based on dataset design and standard elbow heuristic)
optimal_k = 3
kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
df['Cluster'] = kmeans.fit_predict(X_scaled)

# Get cluster centers in original scale for interpretation
centers_scaled = kmeans.cluster_centers_
centers_original = scaler.inverse_transform(centers_scaled)

print(f"\n--- K-Means Clustering Results (K={optimal_k}) ---")
print("Cluster Centers (Original Scale - CGPA, IQ):")
for i, center in enumerate(centers_original):
    print(f"Cluster {i}: CGPA = {center[0]:.2f}, IQ = {center[1]:.2f}")

print("\nCluster Member Counts:")
print(df['Cluster'].value_counts().sort_index())

# 5. Describe Each Cluster
print("\n--- Detailed Cluster Descriptions ---")
for i in range(optimal_k):
    cluster_data = df[df['Cluster'] == i]
    mean_cgpa = cluster_data['CGPA'].mean()
    mean_iq = cluster_data['IQ'].mean()
    count = len(cluster_data)

    print(f"\nCluster {i} ({count} students):")
    print(f"  - Average CGPA: {mean_cgpa:.2f}")
    print(f"  - Average IQ:   {mean_iq:.2f}")
    if mean_cgpa >= 3.4 and mean_iq >= 115:
        description = "High Achievers (Top performers with strong academic grades and cognitive ability)."
    elif mean_cgpa <= 2.9 and mean_iq <= 103:
        description = "Average/Developing Students (Need academic support and mentoring)."
    else:
        description = "Moderate/Balanced Achievers (Solid performance with balanced academic profile)."
    print(f"  - Description:  {description}")

# 6. Visualize Clusters and Save Plot
plt.figure(figsize=(9, 6))
colors = ['purple', 'orange', 'green']
for i in range(optimal_k):
    cluster_subset = df[df['Cluster'] == i]
    plt.scatter(cluster_subset['CGPA'], cluster_subset['IQ'], s=50, c=colors[i], label=f'Cluster {i}', alpha=0.7, edgecolors='k')

# Plot cluster centers
plt.scatter(centers_original[:, 0], centers_original[:, 1], s=250, c='red', marker='X', label='Centroids', edgecolors='black')

plt.title('K-Means Clustering of Students (CGPA vs IQ)')
plt.xlabel('CGPA')
plt.ylabel('IQ')
plt.legend()
plt.grid(True)
plt.savefig('kmeans_student_clusters.png')
plt.close()
print("\nCluster scatter plot saved as kmeans_student_clusters.png")

print("\nK-means student clustering completed successfully!")
