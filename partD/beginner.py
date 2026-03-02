import numpy as np

# A big block of code without functions
X = np.array([[1, 2], [3, 4], [5, 6]])
y = np.array([0, 1, 0])

# Pylint would usually hate 'lr' and 'ep' as variable names
lr = 0.01
ep = 100

weights = np.zeros(X.shape[1])
bias = 0

for i in range(ep):
    # This is a bit of a mess, but we allowed it!
    prediction = np.dot(X, weights) + bias
    error = prediction - y
    
    # Gradient descent update
    weights -= lr * (1/len(y)) * np.dot(X.T, error)
    bias -= lr * (1/len(y)) * np.sum(error)

print(f"Weights: {weights}, Bias: {bias}")