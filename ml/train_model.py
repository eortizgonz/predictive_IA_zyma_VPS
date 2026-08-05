import pandas as pd

import joblib

from sklearn.ensemble import RandomForestClassifier

from sklearn.model_selection import train_test_split

from sklearn.metrics import accuracy_score

data = pd.read_csv("../data/historical_data.csv")

X = data.drop("failure", axis=1)

y = data["failure"]

X_train, X_test, y_train, y_test = train_test_split(

    X,

    y,

    test_size=0.2,

    random_state=42

)

model = RandomForestClassifier(

    n_estimators=250,

    random_state=42

)

model.fit(X_train, y_train)

prediction = model.predict(X_test)

accuracy = accuracy_score(y_test, prediction)

print()

print("--------------------------------")

print("MODEL TRAINED")

print("--------------------------------")

print(f"Accuracy : {accuracy:.3f}")

print("--------------------------------")

joblib.dump(model, "model.pkl")

print()

print("model.pkl generated.")