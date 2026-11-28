import numpy as np

# 1. Arrays (Creation)
print("--- Arrays ---")
arr1 = np.array([1, 2, 3, 4, 5])
arr2 = np.array([[1, 2, 3], [4, 5, 6]])
print("1D Array:", arr1)
print("2D Array:\n", arr2)
print("Zeros:\n", np.zeros((2, 3)))
print("Ones:\n", np.ones((2, 2)))
print("Range:", np.arange(0, 10, 2))
print("Linspace:", np.linspace(0, 1, 5))

# 2. Indexing
print("\n--- Indexing ---")
print("First element:", arr1[0])
print("Element at (1, 2):", arr2[1, 2])

# 3. Slicing
print("\n--- Slicing ---")
print("Slice [1:4]:", arr1[1:4])
print("Slice row 0, all columns:", arr2[0, :])
print("Slice all rows, column 1:", arr2[:, 1])

# 4. Broadcasting
print("\n--- Broadcasting ---")
a = np.array([1, 2, 3])
b = 2
print("a + b:", a + b) # Scalar broadcasting
c = np.array([[10], [20], [30]])
print("c + a:\n", c + a) # Column + Row broadcasting

# 5. Statistics
print("\n--- Statistics ---")
arr_stat = np.array([10, 20, 30, 40, 50])
print("Mean:", np.mean(arr_stat))
print("Median:", np.median(arr_stat))
print("Standard Deviation:", np.std(arr_stat))
print("Sum:", np.sum(arr_stat))
print("Max:", np.max(arr_stat))
print("Min:", np.min(arr_stat))

# 6. Basic Linear Algebra
print("\n--- Basic Linear Algebra ---")
mat_a = np.array([[1, 2], [3, 4]])
mat_b = np.array([[5, 6], [7, 8]])
print("Matrix addition:\n", mat_a + mat_b)
print("Element-wise multiplication:\n", mat_a * mat_b)
print("Matrix multiplication (Dot Product):\n", np.dot(mat_a, mat_b))
print("Transpose:\n", mat_a.T)
print("Inverse:\n", np.linalg.inv(mat_a))
print("Determinant:", np.linalg.det(mat_a))

print("\nNumPy code executed successfully!")
