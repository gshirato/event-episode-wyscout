import pickle


def depickle(path):
    with open(path, "rb") as f:
        return pickle.load(f)


def enpickle(obj, path):
    with open(path, "wb") as f:
        pickle.dump(obj, f)
