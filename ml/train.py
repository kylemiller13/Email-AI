import os
import pandas as pd
import joblib
import numpy as np
import scipy.sparse as sp
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from ml.features import extract_features_from_text, FEATURE_NAMES
import warnings

warnings.filterwarnings("ignore")

# Path constants
DATASET_DIR = os.path.join(os.path.dirname(__file__), "dataset")
MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.pkl")
VECTORIZER_PATH = os.path.join(os.path.dirname(__file__), "vectorizer.pkl")


def load_datasets():
    """Load and combine phishing datasets from CSV files."""
    dfs = []
    
    # List of dataset files to load
    dataset_files = [
        "phishing_email.csv",
        "Enron.csv",
        "Ling.csv",
        "SpamAssasin.csv",
        "CEAS_08.csv",
        "Nazario.csv",
        "Nigerian_Fraud.csv",
    ]
    
    for filename in dataset_files:
        filepath = os.path.join(DATASET_DIR, filename)
        if os.path.exists(filepath):
            try:
                # Try different encodings
                for encoding in ["utf-8", "latin-1", "iso-8859-1"]:
                    try:
                        df = pd.read_csv(filepath, encoding=encoding)
                        print(f"✓ Loaded {filename} ({len(df)} rows)")
                        
                        # Normalize column names to lowercase
                        df.columns = df.columns.str.lower()
                        
                        # Handle different column structures
                        if "text_combined" in df.columns:
                            # phishing_email.csv format
                            dfs.append(df[["text_combined", "label"]].rename(columns={"text_combined": "text"}))
                        elif "text" in df.columns and "label" in df.columns:
                            # Already in correct format
                            dfs.append(df[["text", "label"]])
                        elif "subject" in df.columns and "body" in df.columns and "label" in df.columns:
                            # Combine subject and body
                            df_combined = df.copy()
                            df_combined["text"] = df_combined["subject"] + " " + df_combined["body"]
                            dfs.append(df_combined[["text", "label"]])
                            print(f"  → Combined 'subject' + 'body' columns")
                        elif "class" in df.columns:
                            if "subject" in df.columns and "body" in df.columns:
                                df_combined = df.copy()
                                df_combined["text"] = df_combined["subject"] + " " + df_combined["body"]
                                dfs.append(df_combined[["text", "class"]].rename(columns={"class": "label"}))
                            else:
                                dfs.append(df[[df.columns[0], "class"]].rename(columns={df.columns[0]: "text", "class": "label"}))
                        elif "is_phishing" in df.columns:
                            dfs.append(df[[df.columns[0], "is_phishing"]].rename(columns={df.columns[0]: "text", "is_phishing": "label"}))
                        else:
                            # Try to infer: look for common patterns
                            text_col = None
                            label_col = None
                            
                            # Find text column (subject, body, text, or first column)
                            for col in ["subject", "body", "text", "email"]:
                                if col in df.columns:
                                    text_col = col
                                    break
                            if not text_col and len(df.columns) > 0:
                                text_col = df.columns[0]
                            
                            # Find label column (label, class, is_phishing, etc)
                            for col in ["label", "class", "is_phishing", "category"]:
                                if col in df.columns:
                                    label_col = col
                                    break
                            if not label_col and len(df.columns) > 1:
                                label_col = df.columns[-1]
                            
                            if text_col and label_col:
                                dfs.append(df[[text_col, label_col]].rename(columns={text_col: "text", label_col: "label"}))
                                print(f"  → Inferred columns: '{text_col}' (text), '{label_col}' (label)")
                        break
                    except (UnicodeDecodeError, UnicodeError):
                        continue
            except Exception as e:
                print(f"✗ Could not load {filename}: {e}")
        else:
            print(f"⊘ {filename} not found")
    
    if not dfs:
        raise ValueError("No datasets loaded. Please check dataset directory.")
    
    # Combine all datasets
    combined_df = pd.concat(dfs, ignore_index=True)
    
    # Clean up
    combined_df = combined_df.dropna(subset=["text", "label"])
    combined_df["text"] = combined_df["text"].astype(str).str.strip()
    
    # Normalize labels (case-insensitive, handle common variations)
    label_map = {}
    for label in combined_df["label"].unique():
        lower_label = str(label).lower().strip()
        if "phishing" in lower_label or "spam" in lower_label or "fraud" in lower_label or lower_label in ["1", "true"]:
            label_map[label] = "phishing"
        else:
            label_map[label] = "legitimate"
    
    combined_df["label"] = combined_df["label"].map(label_map)
    
    # Remove any remaining unmapped labels
    combined_df = combined_df.dropna(subset=["label"])
    
    print(f"\nCombined dataset: {len(combined_df)} emails")
    print(f"Phishing: {(combined_df['label'] == 'phishing').sum()}")
    print(f"Legitimate: {(combined_df['label'] == 'legitimate').sum()}")
    
    return combined_df


def build_feature_matrix(texts, vectorizer=None, scaler=None, fit=False):
    """
    Combine engineered features with a small TF-IDF background signal.

    Returns (combined_matrix, vectorizer, scaler)
    """
    print("  → Extracting engineered features...")
    eng_rows = [extract_features_from_text(t)[0] for t in texts]
    eng_matrix = np.vstack(eng_rows)  # (n, len(FEATURE_NAMES))

    if fit:
        scaler = StandardScaler()
        eng_matrix = scaler.fit_transform(eng_matrix)
    else:
        eng_matrix = scaler.transform(eng_matrix)

    print(f"  → Engineered features: {eng_matrix.shape[1]}")

    if fit:
        vectorizer = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 2),
            min_df=3,
            max_df=0.85,
            lowercase=True,
            stop_words="english",
        )
        tfidf_matrix = vectorizer.fit_transform(texts)
    else:
        tfidf_matrix = vectorizer.transform(texts)

    print(f"  → TF-IDF features: {tfidf_matrix.shape[1]}")

    combined = sp.hstack([tfidf_matrix, sp.csr_matrix(eng_matrix)])
    return combined, vectorizer, scaler


def train_model(df):
    """Train engineered-features + TF-IDF hybrid model."""
    print("\n" + "="*60)
    print("TRAINING MODEL")
    print("="*60)

    X = df["text"].values
    y = df["label"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"\nTraining set: {len(X_train)} emails")
    print(f"Test set:     {len(X_test)} emails")

    print("\n→ Building training feature matrix...")
    X_train_mat, vectorizer, scaler = build_feature_matrix(X_train, fit=True)

    print("\n→ Building test feature matrix...")
    X_test_mat, _, _ = build_feature_matrix(X_test, vectorizer=vectorizer, scaler=scaler)

    print(f"\n→ Total features per email: {X_train_mat.shape[1]}")

    print("\n→ Training Logistic Regression classifier...")
    model = LogisticRegression(max_iter=1000, random_state=42, n_jobs=-1, C=1.0)
    model.fit(X_train_mat, y_train)

    print("\n" + "="*60)
    print("MODEL PERFORMANCE")
    print("="*60)

    y_pred = model.predict(X_test_mat)

    accuracy  = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, average="weighted", zero_division=0)
    recall    = recall_score(y_test, y_pred, average="weighted", zero_division=0)
    f1        = f1_score(y_test, y_pred, average="weighted", zero_division=0)

    print(f"\nAccuracy:  {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    print(f"F1 Score:  {f1:.4f}")

    print("\n→ Saving model to", MODEL_PATH)
    joblib.dump({
        "model": model,
        "vectorizer": vectorizer,
        "scaler": scaler,
    }, MODEL_PATH)

    print("✓ Model trained and saved successfully!")
    print("="*60)

    return model, vectorizer, scaler


if __name__ == "__main__":
    print("Loading datasets...")
    df = load_datasets()
    train_model(df)
