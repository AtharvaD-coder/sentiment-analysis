import pandas as pd
import re

def remove_emojis(text):
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)

# Read the XLSX file
df = pd.read_excel('customer_reviews.xlsx', header=None, names=['Review'])

# Remove emojis and clean the text
df['Review'] = df['Review'].apply(remove_emojis)

# Save as CSV
df.to_csv('cleaned_reviews.csv', index=False)

print("Preprocessing complete. Cleaned reviews saved to 'cleaned_reviews.csv'")