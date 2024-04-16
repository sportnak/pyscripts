import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report

# Load the dataset
df = pd.read_csv('./data/urls.csv')

# Filter out rows where the 'text' column is null
df = df[df['text'].notnull()]

# Remove the domain from each of the hrefs in the dataframe
def remove_domain_from_href(href):
    from urllib.parse import urlparse
    parsed_url = urlparse(href)
    return parsed_url.path

df['href'] = df['href'].apply(remove_domain_from_href)


# Combine the href and text columns to form a combined feature
df['combined'] = df['href'] + ' ' + df['text']

# Split the dataset into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(df['combined'], df['category'], test_size=0.3, random_state=42)

print(df)
# Create a pipeline with TF-IDF Vectorizer and Random Forest Classifier
pipeline = Pipeline([
    ('tfidf', TfidfVectorizer()),
    ('clf', RandomForestClassifier(n_estimators=1000, random_state=42))
])

# Train the classifier
pipeline.fit(X_train, y_train)

# Predict the categories of the test set
predictions = pipeline.predict(X_test)

# Print the classification report
print(classification_report(y_test, predictions))

# Function to classify new href/text combos
def classify_url(href, text):
    combined_feature = href + ' ' + text
    return pipeline.predict([combined_feature])[0]

# Check each row categorized as 'news' and run the prediction model on them
news_df = df[df['category'] == 'news']
ids = []
for index, row in news_df.iterrows():
    predicted_category = classify_url(row['href'], row['text'])
    if predicted_category != 'news':
        print(f"Original: news, Predicted: {predicted_category} for row: {index} id: {row['_id']}")
    if predicted_category == 'general':
        ids.append(f"ObjectId('{row['_id']}')")



while True:
    href_input = input("Enter the href (or type 'quit' to stop): ")
    if href_input.lower() == 'quit':
        break
    text_input = input("Enter the text for the href: ")
    if text_input.lower() == 'quit':
        break
    predicted_category = classify_url(href_input, text_input)
    print(f"The predicted category for the URL is: {predicted_category}")


# Example usage:
# new_category = classify_url('https://example.com/new-page', 'This is a new page')
# print(f'The predicted category is: {new_category}')
