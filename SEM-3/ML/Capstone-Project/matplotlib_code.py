import matplotlib
matplotlib.use('Agg') # Use non-interactive backend
import matplotlib.pyplot as plt
import numpy as np

# Sample synthetic data
x = np.linspace(0, 10, 100)
y_sin = np.sin(x)
y_cos = np.cos(x)

categories = ['Category A', 'Category B', 'Category C', 'Category D', 'Category E']
values = [23, 45, 12, 67, 34]

np.random.seed(42)
scatter_x = np.random.rand(50) * 10
scatter_y = np.random.rand(50) * 50
scatter_sizes = np.random.rand(50) * 100 + 20

hist_data = np.random.normal(loc=50, scale=15, size=500)

pie_labels = ['Apples', 'Bananas', 'Cherries', 'Dates', 'Elderberries']
pie_sizes = [30, 25, 20, 15, 10]
pie_colors = ['gold', 'yellowgreen', 'lightcoral', 'lightskyblue', 'violet']

print("--- Matplotlib Charts ---")

# 1. Line Plot
plt.figure(figsize=(8, 5))
plt.plot(x, y_sin, label='Sin(x)', color='blue', linestyle='-', linewidth=2)
plt.plot(x, y_cos, label='Cos(x)', color='red', linestyle='--', linewidth=2)
plt.title('Line Plot: Sine & Cosine Waves', fontsize=14)
plt.xlabel('X axis (radians)', fontsize=12)
plt.ylabel('Y axis (value)', fontsize=12)
plt.legend(loc='upper right')
plt.grid(True)
plt.savefig('matplotlib_line_plot.png')
plt.close()
print("1. Line Plot saved as matplotlib_line_plot.png")

# 2. Bar Plot
plt.figure(figsize=(8, 5))
plt.bar(categories, values, color='teal', alpha=0.7, edgecolor='black', label='Sales')
plt.title('Bar Chart: Sales by Category', fontsize=14)
plt.xlabel('Categories', fontsize=12)
plt.ylabel('Sales Value', fontsize=12)
plt.legend(loc='upper left')
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.savefig('matplotlib_bar_plot.png')
plt.close()
print("2. Bar Plot saved as matplotlib_bar_plot.png")

# 3. Scatter Plot
plt.figure(figsize=(8, 5))
plt.scatter(scatter_x, scatter_y, s=scatter_sizes, c=scatter_y, cmap='viridis', alpha=0.7, edgecolors='w', label='Data Points')
plt.title('Scatter Plot: X vs Y with Varying Sizes', fontsize=14)
plt.xlabel('Feature X', fontsize=12)
plt.ylabel('Feature Y', fontsize=12)
plt.legend(loc='upper left')
plt.colorbar(label='Y Intensity')
plt.grid(True)
plt.savefig('matplotlib_scatter_plot.png')
plt.close()
print("3. Scatter Plot saved as matplotlib_scatter_plot.png")

# 4. Histogram
plt.figure(figsize=(8, 5))
plt.hist(hist_data, bins=25, color='purple', alpha=0.6, edgecolor='black', label='Frequency distribution')
plt.title('Histogram: Normal Distribution', fontsize=14)
plt.xlabel('Value Ranges', fontsize=12)
plt.ylabel('Frequency', fontsize=12)
plt.legend(loc='upper right')
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.savefig('matplotlib_histogram.png')
plt.close()
print("4. Histogram saved as matplotlib_histogram.png")

# 5. Pie Chart
plt.figure(figsize=(7, 7))
plt.pie(pie_sizes, labels=pie_labels, colors=pie_colors, autopct='%1.1f%%', startangle=140, explode=(0.1, 0, 0, 0, 0), shadow=True)
plt.title('Pie Chart: Fruit Market Share', fontsize=14)
plt.legend(pie_labels, title="Fruits", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
plt.tight_layout()
plt.savefig('matplotlib_pie_chart.png')
plt.close()
print("5. Pie Chart saved as matplotlib_pie_chart.png")

# 6. Subplot Charts (Grid of Subplots combining all charts)
fig, axs = plt.subplots(2, 3, figsize=(15, 10))
fig.suptitle('Subplots Overview: Combined Dashboard', fontsize=16)

# Subplot 1: Line
axs[0, 0].plot(x, y_sin, color='blue', label='Sin(x)')
axs[0, 0].set_title('Line Plot')
axs[0, 0].set_xlabel('X')
axs[0, 0].set_ylabel('Y')
axs[0, 0].legend()
axs[0, 0].grid(True)

# Subplot 2: Bar
axs[0, 1].bar(categories, values, color='teal')
axs[0, 1].set_title('Bar Plot')
axs[0, 1].set_xlabel('Categories')
axs[0, 1].set_ylabel('Values')
axs[0, 1].tick_params(axis='x', rotation=30)

# Subplot 3: Scatter
axs[0, 2].scatter(scatter_x, scatter_y, s=30, color='coral', label='Points')
axs[0, 2].set_title('Scatter Plot')
axs[0, 2].set_xlabel('X')
axs[0, 2].set_ylabel('Y')
axs[0, 2].legend()
axs[0, 2].grid(True)

# Subplot 4: Histogram
axs[1, 0].hist(hist_data, bins=20, color='purple', alpha=0.7)
axs[1, 0].set_title('Histogram')
axs[1, 0].set_xlabel('Value')
axs[1, 0].set_ylabel('Frequency')

# Subplot 5: Pie
axs[1, 1].pie(pie_sizes, labels=pie_labels, colors=pie_colors, autopct='%1.0f%%', startangle=90)
axs[1, 1].set_title('Pie Chart')

# Subplot 6: Line vs Cosine (Additional Subplot demo)
axs[1, 2].plot(x, y_cos, color='red', label='Cos(x)')
axs[1, 2].set_title('Cosine Subplot')
axs[1, 2].set_xlabel('X')
axs[1, 2].set_ylabel('Cos(X)')
axs[1, 2].legend()
axs[1, 2].grid(True)

plt.tight_layout()
plt.savefig('matplotlib_subplots.png')
plt.close()
print("6. Subplot Charts saved as matplotlib_subplots.png")

print("\nMatplotlib code executed successfully!")
