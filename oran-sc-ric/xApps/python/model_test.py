# Create a simple pickle file
import pickle

data = {"test": 123}
with open("test.pkl", "wb") as f:
    pickle.dump(data, f)

# Load the pickle file
with open("test.pkl", "rb") as f:
    loaded_data = pickle.load(f)
print(loaded_data)