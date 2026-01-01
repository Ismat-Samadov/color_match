"""
Starbucks Customer & Promotional Analysis
Business-focused insights for optimizing promotional deal strategies
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Set style for professional business charts
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10
COLORS = ['#00704A', '#1E3932', '#D4AF37', '#C8102E', '#F28F1C', '#7C878E']

print("Loading data...")
# Load datasets
portfolio = pd.read_csv('portfolio.csv')
profile = pd.read_csv('profile.csv')
transcript = pd.read_csv('transcript.csv')

# ============================================================================
# DATA PREPARATION
# ============================================================================
print("Preparing data for analysis...")

# Parse channels in portfolio
portfolio['channels'] = portfolio['channels'].apply(lambda x: eval(x) if isinstance(x, str) else x)
portfolio['num_channels'] = portfolio['channels'].apply(len)

# Clean profile data
profile['became_member_on'] = pd.to_datetime(profile['became_member_on'], format='%Y%m%d')
profile['member_years'] = (datetime.now() - profile['became_member_on']).dt.days / 365.25

# Remove customers with missing data for demographic analysis
profile_clean = profile.dropna(subset=['gender', 'income'])

# Age and income segmentation
profile_clean['age_group'] = pd.cut(profile_clean['age'],
                                     bins=[0, 30, 45, 60, 75, 120],
                                     labels=['18-30', '31-45', '46-60', '61-75', '76+'])

profile_clean['income_group'] = pd.cut(profile_clean['income'],
                                        bins=[0, 50000, 75000, 100000, 150000],
                                        labels=['<50K', '50-75K', '75-100K', '100K+'])

# Parse transcript value column
transcript['value_dict'] = transcript['value'].apply(lambda x: json.loads(x.replace("'", '"')))
transcript['offer_id'] = transcript['value_dict'].apply(lambda x: x.get('offer id', x.get('offer_id', None)))
transcript['amount'] = transcript['value_dict'].apply(lambda x: x.get('amount', 0))
transcript['reward'] = transcript['value_dict'].apply(lambda x: x.get('reward', 0))

# Convert time to days
transcript['time_days'] = transcript['time'] / 24

# ============================================================================
# BUSINESS METRIC CALCULATIONS
# ============================================================================
print("Calculating business metrics...")

# 1. OFFER PERFORMANCE METRICS
offer_received = transcript[transcript['event'] == 'offer received']
offer_viewed = transcript[transcript['event'] == 'offer viewed']
offer_completed = transcript[transcript['event'] == 'offer completed']
transactions = transcript[transcript['event'] == 'transaction']

# Merge offer details
offer_performance = portfolio.copy()
offer_performance['received_count'] = offer_received.groupby('offer_id').size().reindex(portfolio['id']).fillna(0).values
offer_performance['viewed_count'] = offer_viewed.groupby('offer_id').size().reindex(portfolio['id']).fillna(0).values
offer_performance['completed_count'] = offer_completed.groupby('offer_id').size().reindex(portfolio['id']).fillna(0).values

offer_performance['view_rate'] = (offer_performance['viewed_count'] / offer_performance['received_count'] * 100).fillna(0)
offer_performance['completion_rate'] = (offer_performance['completed_count'] / offer_performance['received_count'] * 100).fillna(0)
offer_performance['conversion_rate'] = (offer_performance['completed_count'] / offer_performance['viewed_count'] * 100).fillna(0)

# Calculate ROI proxy (completions vs cost)
offer_performance['total_reward_cost'] = offer_performance['completed_count'] * offer_performance['reward']
offer_performance['roi_score'] = offer_performance['completed_count'] / (offer_performance['total_reward_cost'] + 1)

# 2. CUSTOMER SEGMENT PERFORMANCE
# Merge customer data with their transactions
customer_events = transcript.merge(profile_clean, left_on='person', right_on='id', how='inner')

# Customer spending patterns by demographics
customer_spending = customer_events[customer_events['event'] == 'transaction'].groupby('person').agg({
    'amount': ['sum', 'count', 'mean'],
    'gender': 'first',
    'age_group': 'first',
    'income_group': 'first',
    'income': 'first'
}).reset_index()
customer_spending.columns = ['customer_id', 'total_spent', 'transaction_count', 'avg_transaction',
                              'gender', 'age_group', 'income_group', 'income']

# Offer engagement by demographics
offer_engagement = customer_events[customer_events['event'].isin(['offer viewed', 'offer completed'])].groupby('person').agg({
    'event': 'count',
    'gender': 'first',
    'age_group': 'first',
    'income_group': 'first'
}).reset_index()
offer_engagement.columns = ['customer_id', 'offer_interactions', 'gender', 'age_group', 'income_group']

# Merge spending with engagement
customer_profile = customer_spending.merge(offer_engagement, on='customer_id', how='left', suffixes=('', '_y'))
customer_profile['offer_interactions'] = customer_profile['offer_interactions'].fillna(0)
customer_profile = customer_profile[['customer_id', 'total_spent', 'transaction_count', 'avg_transaction',
                                      'offer_interactions', 'gender', 'age_group', 'income_group', 'income']]

# 3. CHANNEL EFFECTIVENESS
# Expand channels
channel_data = []
for _, row in portfolio.iterrows():
    for channel in row['channels']:
        channel_data.append({
            'offer_id': row['id'],
            'channel': channel,
            'offer_type': row['offer_type'],
            'received': offer_performance[offer_performance['id'] == row['id']]['received_count'].values[0],
            'completed': offer_performance[offer_performance['id'] == row['id']]['completed_count'].values[0]
        })
channel_df = pd.DataFrame(channel_data)
channel_performance = channel_df.groupby('channel').agg({
    'received': 'sum',
    'completed': 'sum'
}).reset_index()
channel_performance['completion_rate'] = (channel_performance['completed'] / channel_performance['received'] * 100)

# ============================================================================
# VISUALIZATION 1: Offer Type Performance
# ============================================================================
print("Generating Chart 1: Offer Performance by Type...")

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Completion rates by offer type
offer_type_perf = offer_performance.groupby('offer_type').agg({
    'completion_rate': 'mean',
    'completed_count': 'sum'
}).reset_index()

axes[0].bar(offer_type_perf['offer_type'], offer_type_perf['completion_rate'],
            color=COLORS[:len(offer_type_perf)], edgecolor='black')
axes[0].set_ylabel('Completion Rate (%)')
axes[0].set_xlabel('Offer Type')
axes[0].set_title('Average Completion Rate by Offer Type', fontweight='bold', fontsize=12)
axes[0].grid(axis='y', alpha=0.3)

# Total completions by offer type
axes[1].bar(offer_type_perf['offer_type'], offer_type_perf['completed_count'],
            color=COLORS[:len(offer_type_perf)], edgecolor='black')
axes[1].set_ylabel('Total Completions')
axes[1].set_xlabel('Offer Type')
axes[1].set_title('Total Offer Completions by Type', fontweight='bold', fontsize=12)
axes[1].grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('charts/01_offer_type_performance.png', dpi=300, bbox_inches='tight')
plt.close()

# ============================================================================
# VISUALIZATION 2: Customer Segmentation by Age
# ============================================================================
print("Generating Chart 2: Customer Value by Age Group...")

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Average spending by age group
age_spending = customer_profile.groupby('age_group').agg({
    'total_spent': 'mean',
    'transaction_count': 'mean'
}).reset_index()

axes[0].bar(age_spending['age_group'], age_spending['total_spent'],
            color=COLORS[1], edgecolor='black')
axes[0].set_ylabel('Average Total Spent ($)')
axes[0].set_xlabel('Age Group')
axes[0].set_title('Average Customer Spending by Age Group', fontweight='bold', fontsize=12)
axes[0].grid(axis='y', alpha=0.3)

# Transaction frequency by age
axes[1].bar(age_spending['age_group'], age_spending['transaction_count'],
            color=COLORS[2], edgecolor='black')
axes[1].set_ylabel('Average Transaction Count')
axes[1].set_xlabel('Age Group')
axes[1].set_title('Average Transaction Frequency by Age Group', fontweight='bold', fontsize=12)
axes[1].grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('charts/02_age_segmentation.png', dpi=300, bbox_inches='tight')
plt.close()

# ============================================================================
# VISUALIZATION 3: Income-Based Customer Insights
# ============================================================================
print("Generating Chart 3: Customer Value by Income Level...")

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Spending by income group
income_spending = customer_profile.groupby('income_group').agg({
    'total_spent': 'mean',
    'avg_transaction': 'mean'
}).reset_index()

axes[0].bar(income_spending['income_group'], income_spending['total_spent'],
            color=COLORS[3], edgecolor='black')
axes[0].set_ylabel('Average Total Spent ($)')
axes[0].set_xlabel('Income Group')
axes[0].set_title('Average Customer Spending by Income Level', fontweight='bold', fontsize=12)
axes[0].grid(axis='y', alpha=0.3)

# Average transaction size
axes[1].bar(income_spending['income_group'], income_spending['avg_transaction'],
            color=COLORS[4], edgecolor='black')
axes[1].set_ylabel('Average Transaction Size ($)')
axes[1].set_xlabel('Income Group')
axes[1].set_title('Average Transaction Size by Income Level', fontweight='bold', fontsize=12)
axes[1].grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('charts/03_income_segmentation.png', dpi=300, bbox_inches='tight')
plt.close()

# ============================================================================
# VISUALIZATION 4: Gender-Based Insights
# ============================================================================
print("Generating Chart 4: Customer Behavior by Gender...")

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Spending by gender
gender_spending = customer_profile.groupby('gender').agg({
    'total_spent': 'mean',
    'offer_interactions': 'mean'
}).reset_index()

axes[0].bar(gender_spending['gender'], gender_spending['total_spent'],
            color=[COLORS[0], COLORS[2], COLORS[4]], edgecolor='black')
axes[0].set_ylabel('Average Total Spent ($)')
axes[0].set_xlabel('Gender')
axes[0].set_title('Average Customer Spending by Gender', fontweight='bold', fontsize=12)
axes[0].grid(axis='y', alpha=0.3)

# Offer engagement by gender
axes[1].bar(gender_spending['gender'], gender_spending['offer_interactions'],
            color=[COLORS[0], COLORS[2], COLORS[4]], edgecolor='black')
axes[1].set_ylabel('Average Offer Interactions')
axes[1].set_xlabel('Gender')
axes[1].set_title('Average Offer Engagement by Gender', fontweight='bold', fontsize=12)
axes[1].grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('charts/04_gender_analysis.png', dpi=300, bbox_inches='tight')
plt.close()

# ============================================================================
# VISUALIZATION 5: Channel Effectiveness
# ============================================================================
print("Generating Chart 5: Marketing Channel Performance...")

fig, ax = plt.subplots(figsize=(12, 6))

x = np.arange(len(channel_performance))
width = 0.35

ax.bar(x - width/2, channel_performance['received'], width,
       label='Offers Sent', color=COLORS[0], edgecolor='black')
ax.bar(x + width/2, channel_performance['completed'], width,
       label='Offers Completed', color=COLORS[1], edgecolor='black')

ax.set_ylabel('Number of Offers')
ax.set_xlabel('Marketing Channel')
ax.set_title('Marketing Channel Effectiveness: Sent vs Completed', fontweight='bold', fontsize=12)
ax.set_xticks(x)
ax.set_xticklabels(channel_performance['channel'])
ax.legend()
ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('charts/05_channel_performance.png', dpi=300, bbox_inches='tight')
plt.close()

# ============================================================================
# VISUALIZATION 6: Offer Funnel Analysis
# ============================================================================
print("Generating Chart 6: Offer Conversion Funnel...")

fig, ax = plt.subplots(figsize=(12, 6))

funnel_data = pd.DataFrame({
    'Stage': ['Offers Sent', 'Offers Viewed', 'Offers Completed'],
    'Count': [
        len(offer_received),
        len(offer_viewed),
        len(offer_completed)
    ]
})

funnel_data['Percentage'] = (funnel_data['Count'] / funnel_data['Count'].iloc[0] * 100)

bars = ax.barh(funnel_data['Stage'], funnel_data['Count'], color=COLORS[:3], edgecolor='black')

# Add percentage labels
for i, (count, pct) in enumerate(zip(funnel_data['Count'], funnel_data['Percentage'])):
    ax.text(count, i, f'  {count:,} ({pct:.1f}%)', va='center', fontweight='bold')

ax.set_xlabel('Number of Customers')
ax.set_title('Promotional Offer Conversion Funnel', fontweight='bold', fontsize=12)
ax.grid(axis='x', alpha=0.3)

plt.tight_layout()
plt.savefig('charts/06_conversion_funnel.png', dpi=300, bbox_inches='tight')
plt.close()

# ============================================================================
# VISUALIZATION 7: Offer Difficulty vs Completion
# ============================================================================
print("Generating Chart 7: Offer Difficulty Impact...")

fig, ax = plt.subplots(figsize=(12, 6))

difficulty_perf = offer_performance.groupby('difficulty').agg({
    'completion_rate': 'mean',
    'received_count': 'sum'
}).reset_index()

ax.bar(difficulty_perf['difficulty'].astype(str), difficulty_perf['completion_rate'],
       color=COLORS[0], edgecolor='black')
ax.set_ylabel('Average Completion Rate (%)')
ax.set_xlabel('Offer Difficulty (Minimum Spend Required $)')
ax.set_title('Impact of Offer Difficulty on Completion Rate', fontweight='bold', fontsize=12)
ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('charts/07_difficulty_analysis.png', dpi=300, bbox_inches='tight')
plt.close()

# ============================================================================
# VISUALIZATION 8: Offer Duration Analysis
# ============================================================================
print("Generating Chart 8: Offer Duration Impact...")

fig, ax = plt.subplots(figsize=(12, 6))

duration_perf = offer_performance.groupby('duration').agg({
    'completion_rate': 'mean',
    'view_rate': 'mean'
}).reset_index()

x = np.arange(len(duration_perf))
width = 0.35

ax.bar(x - width/2, duration_perf['view_rate'], width,
       label='View Rate', color=COLORS[2], edgecolor='black')
ax.bar(x + width/2, duration_perf['completion_rate'], width,
       label='Completion Rate', color=COLORS[3], edgecolor='black')

ax.set_ylabel('Rate (%)')
ax.set_xlabel('Offer Duration (Days)')
ax.set_title('Impact of Offer Duration on Engagement', fontweight='bold', fontsize=12)
ax.set_xticks(x)
ax.set_xticklabels(duration_perf['duration'].astype(int))
ax.legend()
ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('charts/08_duration_analysis.png', dpi=300, bbox_inches='tight')
plt.close()

# ============================================================================
# VISUALIZATION 9: High-Value Customer Segments
# ============================================================================
print("Generating Chart 9: High-Value Customer Identification...")

# Create customer value segments
customer_profile['customer_value'] = pd.qcut(customer_profile['total_spent'],
                                               q=4,
                                               labels=['Low', 'Medium', 'High', 'Very High'])

value_segment = customer_profile.groupby('customer_value').agg({
    'total_spent': 'mean',
    'customer_id': 'count'
}).reset_index()
value_segment.columns = ['Value Segment', 'Avg Spending', 'Customer Count']

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Average spending by segment
axes[0].bar(value_segment['Value Segment'], value_segment['Avg Spending'],
            color=COLORS[:4], edgecolor='black')
axes[0].set_ylabel('Average Total Spent ($)')
axes[0].set_xlabel('Customer Value Segment')
axes[0].set_title('Average Spending by Customer Value Segment', fontweight='bold', fontsize=12)
axes[0].grid(axis='y', alpha=0.3)

# Customer distribution
axes[1].bar(value_segment['Value Segment'], value_segment['Customer Count'],
            color=COLORS[:4], edgecolor='black')
axes[1].set_ylabel('Number of Customers')
axes[1].set_xlabel('Customer Value Segment')
axes[1].set_title('Customer Distribution by Value Segment', fontweight='bold', fontsize=12)
axes[1].grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('charts/09_customer_value_segments.png', dpi=300, bbox_inches='tight')
plt.close()

# ============================================================================
# VISUALIZATION 10: Cross-Segment Offer Response
# ============================================================================
print("Generating Chart 10: Offer Response by Customer Segment...")

# Get offer completion data by customer
completed_offers = customer_events[customer_events['event'] == 'offer completed'].copy()
segment_offer_response = completed_offers.groupby(['age_group', 'income_group']).size().reset_index(name='completions')

# Create heatmap data
heatmap_data = segment_offer_response.pivot(index='age_group', columns='income_group', values='completions').fillna(0)

fig, ax = plt.subplots(figsize=(12, 8))
sns.heatmap(heatmap_data, annot=True, fmt='.0f', cmap='YlGn', cbar_kws={'label': 'Offer Completions'},
            linewidths=0.5, ax=ax)
ax.set_title('Offer Completions by Age and Income Segment', fontweight='bold', fontsize=12)
ax.set_xlabel('Income Group')
ax.set_ylabel('Age Group')

plt.tight_layout()
plt.savefig('charts/10_segment_offer_response.png', dpi=300, bbox_inches='tight')
plt.close()

# ============================================================================
# VISUALIZATION 11: Transaction Patterns
# ============================================================================
print("Generating Chart 11: Transaction Volume Over Time...")

# Transaction volume over time
transaction_timeline = transactions.copy()
transaction_timeline['time_week'] = (transaction_timeline['time'] / 24 / 7).astype(int)
weekly_transactions = transaction_timeline.groupby('time_week').agg({
    'amount': ['sum', 'count', 'mean']
}).reset_index()
weekly_transactions.columns = ['Week', 'Total Revenue', 'Transaction Count', 'Avg Transaction']

fig, axes = plt.subplots(2, 1, figsize=(14, 10))

# Revenue over time
axes[0].plot(weekly_transactions['Week'], weekly_transactions['Total Revenue'],
             color=COLORS[0], linewidth=2, marker='o', markersize=4)
axes[0].set_ylabel('Total Revenue ($)')
axes[0].set_xlabel('Week')
axes[0].set_title('Weekly Revenue Trend', fontweight='bold', fontsize=12)
axes[0].grid(alpha=0.3)

# Transaction count over time
axes[1].plot(weekly_transactions['Week'], weekly_transactions['Transaction Count'],
             color=COLORS[3], linewidth=2, marker='o', markersize=4)
axes[1].set_ylabel('Number of Transactions')
axes[1].set_xlabel('Week')
axes[1].set_title('Weekly Transaction Volume', fontweight='bold', fontsize=12)
axes[1].grid(alpha=0.3)

plt.tight_layout()
plt.savefig('charts/11_transaction_trends.png', dpi=300, bbox_inches='tight')
plt.close()

# ============================================================================
# VISUALIZATION 12: ROI Analysis by Offer Type
# ============================================================================
print("Generating Chart 12: Promotional ROI Analysis...")

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Cost vs completions by offer type
offer_roi = offer_performance.groupby('offer_type').agg({
    'total_reward_cost': 'sum',
    'completed_count': 'sum'
}).reset_index()

axes[0].bar(offer_roi['offer_type'], offer_roi['total_reward_cost'],
            color=COLORS[4], edgecolor='black')
axes[0].set_ylabel('Total Reward Cost ($)')
axes[0].set_xlabel('Offer Type')
axes[0].set_title('Total Promotional Cost by Offer Type', fontweight='bold', fontsize=12)
axes[0].grid(axis='y', alpha=0.3)

# Efficiency: completions per dollar spent
offer_roi['efficiency'] = offer_roi['completed_count'] / (offer_roi['total_reward_cost'] + 1)
axes[1].bar(offer_roi['offer_type'], offer_roi['efficiency'],
            color=COLORS[1], edgecolor='black')
axes[1].set_ylabel('Completions per Dollar Spent')
axes[1].set_xlabel('Offer Type')
axes[1].set_title('Promotional Efficiency by Offer Type', fontweight='bold', fontsize=12)
axes[1].grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('charts/12_roi_analysis.png', dpi=300, bbox_inches='tight')
plt.close()

# ============================================================================
# SUMMARY STATISTICS FOR BUSINESS REPORT
# ============================================================================
print("\n" + "="*80)
print("KEY BUSINESS METRICS SUMMARY")
print("="*80)

print(f"\nCustomer Base:")
print(f"  Total Customers: {len(profile):,}")
print(f"  Customers with Complete Data: {len(profile_clean):,} ({len(profile_clean)/len(profile)*100:.1f}%)")
print(f"  Data Quality Gap: {len(profile) - len(profile_clean):,} customers ({(len(profile) - len(profile_clean))/len(profile)*100:.1f}%)")

print(f"\nOffer Performance:")
print(f"  Total Offers Sent: {len(offer_received):,}")
print(f"  View Rate: {len(offer_viewed)/len(offer_received)*100:.1f}%")
print(f"  Completion Rate: {len(offer_completed)/len(offer_received)*100:.1f}%")
print(f"  Conversion Rate (Viewed to Completed): {len(offer_completed)/len(offer_viewed)*100:.1f}%")

print(f"\nTransaction Metrics:")
print(f"  Total Transactions: {len(transactions):,}")
print(f"  Total Revenue: ${transactions['amount'].sum():,.2f}")
print(f"  Average Transaction: ${transactions['amount'].mean():.2f}")

print(f"\nBest Performing Offer Type:")
best_offer = offer_type_perf.loc[offer_type_perf['completion_rate'].idxmax()]
print(f"  Type: {best_offer['offer_type']}")
print(f"  Completion Rate: {best_offer['completion_rate']:.1f}%")

print(f"\nMost Valuable Customer Segment (by avg spending):")
best_age = age_spending.loc[age_spending['total_spent'].idxmax()]
print(f"  Age Group: {best_age['age_group']}")
print(f"  Average Spending: ${best_age['total_spent']:.2f}")

best_income = income_spending.loc[income_spending['total_spent'].idxmax()]
print(f"  Income Group: {best_income['income_group']}")
print(f"  Average Spending: ${best_income['total_spent']:.2f}")

print(f"\nChannel Performance:")
for _, row in channel_performance.iterrows():
    print(f"  {row['channel']}: {row['completion_rate']:.1f}% completion rate")

print("\n" + "="*80)
print("All charts generated successfully in the 'charts/' directory!")
print("="*80)
