import os
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from nltk.corpus import movie_reviews
import nltk

# Ensure NLTK data is downloaded
nltk.download('movie_reviews')

# Load dataset
def load_data():
    fileids = movie_reviews.fileids()
    texts = [movie_reviews.raw(fileid) for fileid in fileids]
    labels = [fileid.split('/')[0] for fileid in fileids]
    return texts, labels

# Create and train the NLP model
def train_model():
    texts, labels = load_data()
    X_train, X_test, y_train, y_test = train_test_split(texts, labels, test_size=0.2, random_state=42)

    # Define a pipeline with TF-IDF and Multinomial Naive Bayes
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(stop_words='english', max_features=5000)),
        ('classifier', MultinomialNB())
    ])

    # Train the model
    pipeline.fit(X_train, y_train)

    # Test the model
    y_pred = pipeline.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Model Accuracy: {accuracy:.2f}")

    return pipeline

# Save the model to a .pkl file
def save_model(model, filename='ai_models/nlp_model_v1.pkl'):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'wb') as file:
        pickle.dump(model, file)
    print(f"Model saved to {filename}")

if __name__ == "__main__":
    print("Training NLP Model...")
    model = train_model()
    print("Saving NLP Model...")
    save_model(model)
    print("NLP Model has been successfully saved.")
