import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix
import random
from datetime import datetime, timedelta
import joblib

# Step 1: Generate synthetic data with COVID-19 specific outbreak labeling
def generate_synthetic_data(num_samples=100):
    data = []
    locations = ['Limingantulli', 'Kaukovainio', 'Oulunsalo']
    symptoms_list = [['Nausea', 'Sweating'], ['Fatigue', 'Headache'], ['Cough', 'Fever'], []]
    test_types = ['COVID-19']
    viral_loads = ['undetectable', 'detectable']
    viral_statuses = ['viral-negative', 'viral-positive']
    hospitalization_statuses = ['not-hospitalized', 'hospitalized']
    test_centers = ['SynLab']

    for i in range(num_samples):
        user_id = f"user_{i}"
        checkin_timestamp = (datetime.now() - timedelta(days=random.randint(0, 5))).isoformat()
        checkin_location = random.choice(locations)
        symptoms = random.choice(symptoms_list)

        lab_report_timestamp = (datetime.now() - timedelta(days=random.randint(0, 5))).isoformat()
        test_type = random.choice(test_types)
        result = random.choice(['positive', 'negative'])
        viral_load = random.choice(viral_loads)
        viral_status = random.choice(viral_statuses)
        hospitalization_status = random.choice(hospitalization_statuses)
        test_center = random.choice(test_centers)

        # Define outbreak based only on COVID-19 viral-positive cases
        outbreak = 1 if (test_type == 'COVID-19' and viral_status == 'viral-positive') else 0

        sample = {
            'userId': user_id,
            'checkin': {'timestamp': checkin_timestamp, 'location': checkin_location, 'symptoms': symptoms},
            'labReport': {'testType': test_type, 'testDate': lab_report_timestamp, 'result': result,
                          'viralLoad': viral_load, 'viralStatus': viral_status,
                          'hospitalizationStatus': hospitalization_status, 'testCenter': test_center},
            'outbreak': outbreak
        }
        data.append(sample)
    
    return data

# Generate synthetic data
synthetic_data = generate_synthetic_data(1000)

# Step 2: Preprocess the data
def preprocess_data(data):
    processed_data = []
    for entry in data:
        checkin = entry['checkin']
        lab_report = entry['labReport']
        
        row = {
            'location': checkin['location'],
            'symptoms': ','.join(checkin['symptoms']),
            'testType': lab_report['testType'],
            'result': lab_report['result'],
            'viralLoad': lab_report['viralLoad'],
            'viralStatus': lab_report['viralStatus'],
            'hospitalizationStatus': lab_report['hospitalizationStatus'],
            'testCenter': lab_report['testCenter'],
            'outbreak': entry['outbreak']
        }
        processed_data.append(row)

    return pd.DataFrame(processed_data)

# Convert to DataFrame
df = preprocess_data(synthetic_data)

# Step 3: Encode categorical variables
def encode_data(df):
    le = LabelEncoder()
    df['location'] = le.fit_transform(df['location'])
    df['testType'] = le.fit_transform(df['testType'])
    df['result'] = le.fit_transform(df['result'])
    df['viralLoad'] = le.fit_transform(df['viralLoad'])
    df['viralStatus'] = le.fit_transform(df['viralStatus'])
    df['hospitalizationStatus'] = le.fit_transform(df['hospitalizationStatus'])
    df['testCenter'] = le.fit_transform(df['testCenter'])
    df['symptoms'] = df['symptoms'].apply(lambda x: len(x.split(',')))
    return df

df = encode_data(df)

# Step 4: Prepare training data
X = df.drop(columns=['outbreak'])
y = df['outbreak']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Step 5: Train the updated model
model = RandomForestClassifier(random_state=42)
model.fit(X_train, y_train)

# Step 6: Evaluate performance
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
conf_matrix = confusion_matrix(y_test, y_pred)

print(f"Accuracy: {accuracy:.4f}")
print("Confusion Matrix:")
print(conf_matrix)

# Step 7: Save the model
joblib.dump(model, 'outbreak_prediction_model.pkl')