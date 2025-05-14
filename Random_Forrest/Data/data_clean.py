import pandas as pd
import re

# --- Load CSV ---
df = pd.read_csv("match_stats.csv")  # Replace with your actual file
skipped = []

# --- Column groups ---
percent_cols = [
    'DF%', '1stIn', '1st%', '2nd%',
    'Ret_TPW', 'Ret_RPW', 'Ret_vA%',
    'Ret_v1st%', 'Ret_v2nd%'  # Ret_BPCnv is handled separately
]
fraction_cols = ['Ret_BPCnv']
time_cols = ['Ret_Time']
categorical_cols = ['Surface', 'Rd']

# --- Safe percent conversion ---
def safe_percent_to_float(x, col):
    if isinstance(x, str):
        x = x.strip().replace('%', '')
        if x in ['-', '']:
            skipped.append((col, x))
            return None
        try:
            return float(x) / 100
        except:
            skipped.append((col, x))
            return None
    return x

for col in percent_cols:
    if col in df.columns:
        df[col] = df[col].apply(lambda x: safe_percent_to_float(x, col))

# --- Safe fraction conversion with 0/0 → 0 ---
def safe_frac_to_float(x, col):
    if isinstance(x, str) and '/' in x:
        try:
            num, denom = map(int, x.split('/'))
            if denom == 0:
                return 0.0 if num == 0 else None
            return round(num / denom, 2)
        except:
            skipped.append((col, x))
            return None
    return x

for col in fraction_cols:
    if col in df.columns:
        df[col] = df[col].apply(lambda x: safe_frac_to_float(x, col))

# --- Safe time conversion (M:SS to float minutes) ---
def safe_time_to_minutes(x, col):
    if isinstance(x, str) and ':' in x:
        try:
            mins, secs = map(int, x.split(':'))
            return round(mins + secs / 60, 2)
        except:
            skipped.append((col, x))
            return None
    return x

for col in time_cols:
    if col in df.columns:
        df[col] = df[col].apply(lambda x: safe_time_to_minutes(x, col))

# --- Calculate total games from score string ---
def calculate_total_games(score_str):
    if not isinstance(score_str, str):
        return None
    total_games = 0
    clean_score = score_str.replace('RET', '').strip()
    sets = clean_score.split()
    for s in sets:
        s = re.sub(r'\(.*?\)', '', s)
        try:
            g1, g2 = map(int, s.split('-'))
            total_games += g1 + g2
        except:
            continue
    return total_games

if 'Score' in df.columns:
    df['Total_Games'] = df['Score'].apply(calculate_total_games)

# --- One-hot encode categorical columns (Surface and Rd) ---
for col in categorical_cols:
    if col in df.columns:
        dummies = pd.get_dummies(df[col], prefix=col)
        df = pd.concat([df.drop(columns=[col]), dummies], axis=1)

# --- Clean and convert Date column with non-breaking hyphen fix ---
if 'Date' in df.columns:
    try:
        print(" Preview raw Date values:", df['Date'].head(5).tolist())
        df['Date'] = df['Date'].astype(str).str.replace('‑', '-', regex=False)  # Replace non-breaking hyphen
        df['Date'] = pd.to_datetime(df['Date'], format='%d-%b-%Y', errors='coerce')
        print(" Parsed", df['Date'].notna().sum(), "valid dates out of", len(df))
        df = df.sort_values(by='Date')  # Sort ascending (oldest → newest)
    except Exception as e:
        print(" Failed to sort by Date:", e)
else:
    print(" 'Date' column not found!")

# --- Final check and save ---
print(" Final columns:", df.columns.tolist())
print(" Preview cleaned data:\n", df.head())

# Save cleaned CSV
df.to_csv("cleaned_output.csv", index=False)
print(" Cleaned and sorted data saved to 'cleaned_output.csv'")

# Save skipped values log
with open("skipped_log.txt", "w", encoding="utf-8") as f:
    f.write("Column\tSkipped Value\n")
    for col, val in skipped:
        f.write(f"{col}\t{val}\n")

print(f"  {len(skipped)} problematic values logged to 'skipped_log.txt'")
