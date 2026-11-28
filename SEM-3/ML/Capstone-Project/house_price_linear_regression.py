import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# 1. Generate Synthetic Dataset
np.random.seed(42)
n_samples = 200

area = np.random.normal(1500, 400, n_samples).clip(500, 4000)
bedrooms = np.random.randint(1, 6, n_samples)
age = np.random.randint(0, 50, n_samples)
distance = np.random.uniform(1, 30, n_samples)

# Price formula with linear relationship + noise
# Price = 50,000 + 150*area + 10,000*bedrooms - 1,200*age - 2,000*distance + noise
price = (
    50000
    + 150 * area
    + 10000 * bedrooms
    - 1200 * age
    - 2000 * distance
    + np.random.normal(0, 15000, n_samples)
)

df = pd.DataFrame({
    'Area': area,
    'Bedrooms': bedrooms,
    'Age': age,
    'Distance': distance,
    'Price': price
})

print("--- House Price Dataset Summary ---")
print(df.head())
print("\nDataset Info:")
print(df.info())

# 2. Features and Target Split
X = df[['Area', 'Bedrooms', 'Age', 'Distance']]
y = df['Price']

# 3. Train-Test Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 4. Model Training
model = LinearRegression()
model.fit(X_train, y_train)

# 5. Model Evaluation
y_pred = model.predict(X_test)

mae = mean_absolute_error(y_test, y_pred)
mse = mean_squared_error(y_test, y_pred)
rmse = np.sqrt(mse)
r2 = r2_score(y_test, y_pred)

print("\n--- Model Coefficients ---")
for feature, coef in zip(X.columns, model.coef_):
    print(f"{feature}: {coef:.2f}")
print(f"Intercept: {model.intercept_:.2f}")

print("\n--- Evaluation Metrics ---")
print(f"Mean Absolute Error (MAE): ${mae:,.2f}")
print(f"Root Mean Squared Error (RMSE): ${rmse:,.2f}")
print(f"R-squared (R2 Score): {r2:.4f}")

print("\nHouse price linear regression completed successfully!")
