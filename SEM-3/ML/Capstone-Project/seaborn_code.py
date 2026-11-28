import matplotlib
matplotlib.use('Agg') # Use non-interactive backend to avoid hanging on GUI display
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Load built-in dataset
tips = sns.load_dataset("tips")
iris = sns.load_dataset("iris")

print("--- Seaborn Statistical Plots ---")

# 1. Histogram (using histplot)
plt.figure(figsize=(10, 6))
sns.histplot(data=tips, x="total_bill", kde=True, color="skyblue")
plt.title("Histogram of Total Bill (with KDE)")
plt.savefig("seaborn_histplot.png")
plt.close()
print("1. Histogram saved as seaborn_histplot.png")

# 2. Box Plot
plt.figure(figsize=(10, 6))
sns.boxplot(data=tips, x="day", y="total_bill", hue="sex", palette="Set2")
plt.title("Box Plot of Total Bill by Day and Sex")
plt.savefig("seaborn_boxplot.png")
plt.close()
print("2. Box Plot saved as seaborn_boxplot.png")

# 3. Violin Plot
plt.figure(figsize=(10, 6))
sns.violinplot(data=tips, x="day", y="total_bill", hue="sex", split=True, palette="Pastel1")
plt.title("Violin Plot of Total Bill by Day and Sex")
plt.savefig("seaborn_violinplot.png")
plt.close()
print("3. Violin Plot saved as seaborn_violinplot.png")

# 4. Scatter Plot
plt.figure(figsize=(10, 6))
sns.scatterplot(data=tips, x="total_bill", y="tip", hue="time", style="time", size="size")
plt.title("Scatter Plot: Total Bill vs Tip")
plt.savefig("seaborn_scatterplot.png")
plt.close()
print("4. Scatter Plot saved as seaborn_scatterplot.png")

# 5. Heatmap
plt.figure(figsize=(8, 6))
numeric_tips = tips.select_dtypes(include=[np.number])
corr = numeric_tips.corr()
sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f")
plt.title("Heatmap of Correlation Matrix (Tips Dataset)")
plt.savefig("seaborn_heatmap.png")
plt.close()
print("5. Heatmap saved as seaborn_heatmap.png")

# 6. Pairplot
pp = sns.pairplot(iris, hue="species", markers=["o", "s", "D"])
pp.figure.suptitle("Pairplot of Iris Dataset", y=1.02)
pp.savefig("seaborn_pairplot.png")
plt.close('all')
print("6. Pairplot saved as seaborn_pairplot.png")

print("\nSeaborn code executed successfully!")
