
import pandas as pd
import urllib
from fuzzywuzzy import fuzz

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.feature_extraction.text import CountVectorizer
from scipy.spatial.distance import jaccard
import numpy as np

# Load the CSV file into a DataFrame
df = pd.read_csv('./data/training/urls.csv', dtype={'href': str, 'text': str})

# Function to extract domain from URL
def extract_path(url):
    try:
        parsed_url = urllib.parse.urlparse(url)
        domain_parts = parsed_url.netloc.split('.')
        # Ignore subdomains to extract the main domain
        # domain = '.'.join(domain_parts[-2:]) if len(domain_parts) > 1 else domain_parts[0]
        return parsed_url.path        
    except Exception as e:
        print(f"Error parsing URL '{url}': {e}")
        domain = url
    return domain


# Apply the function to extract domain and create a new column
df['path'] = df['href'].apply(extract_path)

# Custom domain to compute string distance against
custom_domain = 'churchillcountynv.com'

# Function to compute Jaccard string distance

def compute_string_distance(domain1, domain2):
    return fuzz.ratio(domain1, domain2) / 100

# Compute the string distance and create a new column
# df['domain_distance'] = df['domain'].apply(lambda x: compute_string_distance(x, custom_domain))

# Prepare the data for the random forest classifier
vectorizer = CountVectorizer()
X_text = vectorizer.fit_transform(df['text'])
X_path = vectorizer.fit_transform(df['path'])
# X_domain_distance = np.array(df['domain_distance']).reshape(-1, 1)
X = np.hstack((X_text.toarray(),  X_path.toarray())) #, X_domain_distance))

print(df['path'])
# Encode the labels
y = df['type'].astype('category').cat.codes

# Split the dataset into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.5, random_state=42)

# Initialize the Random Forest Classifier
rf_classifier = RandomForestClassifier(n_estimators=500, random_state=42)

# Train the classifier
rf_classifier.fit(X_train, y_train)

# Predict on the test set
y_pred = rf_classifier.predict(X_test)

# Calculate the accuracy
accuracy = accuracy_score(y_test, y_pred)
print(f'Accuracy: {accuracy:.2f}')

# End Generation Here
