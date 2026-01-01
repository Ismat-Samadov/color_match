import pandas as pd
import json

# Load the datasets
portfolio = pd.read_csv('portfolio.csv')
profile = pd.read_csv('profile.csv')
transcript = pd.read_csv('transcript.csv')

print("=" * 80)
print("PORTFOLIO DATA (Promotional Offers)")
print("=" * 80)
print(f"Shape: {portfolio.shape}")
print(f"\nColumns: {list(portfolio.columns)}")
print(f"\nFirst few rows:")
print(portfolio.head())
print(f"\nData types:")
print(portfolio.dtypes)
print(f"\nUnique offers: {portfolio.shape[0]}")

print("\n" + "=" * 80)
print("PROFILE DATA (Customer Demographics)")
print("=" * 80)
print(f"Shape: {profile.shape}")
print(f"\nColumns: {list(profile.columns)}")
print(f"\nFirst few rows:")
print(profile.head())
print(f"\nData types:")
print(profile.dtypes)
print(f"\nMissing values:")
print(profile.isnull().sum())
print(f"\nBasic statistics:")
print(profile.describe())

print("\n" + "=" * 80)
print("TRANSCRIPT DATA (Transactions & Interactions)")
print("=" * 80)
print(f"Shape: {transcript.shape}")
print(f"\nColumns: {list(transcript.columns)}")
print(f"\nFirst few rows:")
print(transcript.head(10))
print(f"\nData types:")
print(transcript.dtypes)
print(f"\nEvent types:")
print(transcript['event'].value_counts())

# Parse value column if it's JSON
if transcript['value'].dtype == 'object':
    print("\nSample value column (JSON):")
    for i in range(min(5, len(transcript))):
        try:
            print(f"{i}: {transcript.iloc[i]['value']}")
        except:
            pass
