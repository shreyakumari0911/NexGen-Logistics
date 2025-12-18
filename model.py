import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, roc_auc_score, confusion_matrix

def train_delay_model(df):
    df = df.copy()

    df["delayed"] = (df["actual_delivery_days"] > df["expected_delivery_days"]).astype(int)

    features = [
        "route_distance_km",
        "vehicle_capacity",
        "warehouse_load",
        "delivery_priority",
        "fuel_cost",
        "maintenance_cost"
    ]

    # Create a copy with only needed features
    df_model = df[features + ["delayed"]].copy()
    df_model = df_model.dropna()

    # Store encoders for later use
    encoders = {}
    for col in df_model.select_dtypes(include="object").columns:
        enc = LabelEncoder()
        df_model[col] = enc.fit_transform(df_model[col])
        encoders[col] = enc

    # Ensure all features are numeric
    for col in features:
        df_model[col] = pd.to_numeric(df_model[col], errors="coerce")
    df_model = df_model.dropna()

    X = df_model[features]
    y = df_model["delayed"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=10,
        min_samples_leaf=5,
        random_state=42,
        class_weight="balanced"
    )

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "roc_auc": roc_auc_score(y_test, y_prob),
        "confusion_matrix": confusion_matrix(y_test, y_pred),
        "feature_importance": pd.Series(
            model.feature_importances_, index=features
        ).sort_values(ascending=False)
    }

    return model, features, encoders, metrics
