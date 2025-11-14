import pandas as pd
import random
from flask import Flask, jsonify, request
from flask_cors import CORS
from pytrends.request import TrendReq
from datetime import datetime, timedelta

# --- 1. Flask App Setup ---
app = Flask(__name__)
# Allow all origins (perfect for a hackathon, but not for production)
CORS(app)

# --- 2. Cache Configuration ---
# This is our simple in-memory cache to avoid Google's 429 error
trends_cache = {}
CACHE_DURATION = timedelta(minutes=10) # Store data for 10 minutes

# --- 3. Disease Keyword Configuration ---
DISEASE_KEYWORDS = {
    'flu': {
        'keywords': ['flu symptoms', 'fever and cough', 'influenza treatment', 'Tamifu'],
        'baseline_factor': 1.2
    },
    'dengue': {
        'keywords': ['dengue symptoms', 'mosquito bite fever', 'platelet count low', 'dengue treatment'],
        'baseline_factor': 1.5
    },
    'covid': {
        'keywords': ['covid symptoms', 'loss of smell', 'covid test near me', 'Paxlovid'],
        'baseline_factor': 1.3
    }
}

# --- 4. Data Source 1: Google Trends (with Caching) ---
def get_google_trends(disease_config, geo):
    """
    Fetches Google Trends data, using a cache to avoid rate limits.
    Returns a tuple: (pandas_dataframe, chart_js_data_dict)
    """
    
    # --- Cache Check Logic ---
    # 1. Create a unique key for this request
    cache_key = f"{geo}_{'_'.join(disease_config['keywords'])}"
    
    # 2. Check if a valid, non-expired entry exists
    if cache_key in trends_cache:
        entry = trends_cache[cache_key]
        if datetime.now() - entry['timestamp'] < CACHE_DURATION:
            print(f"[Cache] HIT! Serving cached data for {cache_key}.")
            return entry['data'], entry['chart_data']
        else:
            print(f"[Cache] STALE. Entry for {cache_key} expired.")
    else:
        print(f"[Cache] MISS. No data for {cache_key}.")
        
    print(f"[Trends] Fetching LIVE Google Trends data for geo={geo}...")
    
    try:
        # A. Initialize Pytrends
        pytrends = TrendReq(hl='en-US', tz=360, timeout=(10, 25))
        
        # B. Define the time window (Last 30 days)
        timeframe = 'today 1-m' # 1-m means "one month"
        
        # C. Build the query payload
        pytrends.build_payload(
            kw_list=disease_config['keywords'],
            cat=0,
            timeframe=timeframe,
            geo=geo,
            gprop=''
        )
        
        # D. Make the API call
        trends_df = pytrends.interest_over_time()

        if trends_df.empty:
            print("[Trends] No data returned from Google Trends.")
            # Cache the "no data" result so we don't ask again
            trends_cache[cache_key] = {
                'timestamp': datetime.now(),
                'data': None,
                'chart_data': None
            }
            return None, None

        # E. Prepare data for Chart.js (for Person 2)
        chart_data = {
            'labels': trends_df.index.strftime('%Y-%m-%d').tolist(), # X-axis
            'datasets': []
        }
        
        # Add all keywords to the chart dataset
        for keyword in disease_config['keywords']:
            if keyword in trends_df.columns:
                chart_data['datasets'].append({
                    'label': keyword,
                    'data': trends_df[keyword].tolist()
                })
        
        print("[Trends] Successfully fetched and processed Google Trends data.")
        
        # --- Store in Cache ---
        # 3. Store the new, good data in our cache
        trends_cache[cache_key] = {
            'timestamp': datetime.now(),
            'data': trends_df,
            'chart_data': chart_data
        }
        
        return trends_df, chart_data

    except Exception as e:
        print(f"[Trends] !!! ERROR: Failed to get Google Trends data: {e}")
        # Return empty/null objects so the app doesn't crash
        return None, None

# --- 5. Data Source 2: Social Media (Mocked) ---
def get_social_chatter(disease_config, city):
    """
    MOCK FUNCTION
    Simulates scanning Reddit for chatter.
    """
    print(f"[MOCK] Simulating Reddit scan for '{city}'... (returning a random score)")
    # Return a random score to make the demo dynamic
    return random.randint(5, 50)

# --- 6. Core Logic: Threat Score Calculation ---
def calculate_threat_score(trends_df, social_score, disease_config):
    """
    Calculates a "Threat Score" based on the data.
    """
    if trends_df is None or trends_df.empty:
        return 0, "Low", "No trend data available for calculation."

    try:
        # A. Calculate Baseline (avg of all keywords in first 23 days)
        baseline_df = trends_df[:-7]
        if baseline_df.empty:
            # If no baseline, set a small default to avoid division by zero
            baseline_avg = 10 
        else:
            # Sum all keyword columns, then take the mean
            baseline_avg = baseline_df[disease_config['keywords']].sum(axis=1).mean()
        
        # B. Calculate Current Spike (avg of all keywords in last 7 days)
        current_df = trends_df[-7:]
        current_avg = current_df[disease_config['keywords']].sum(axis=1).mean()
        
        # C. Calculate Trend Score (percentage increase)
        trend_score = 0
        if baseline_avg > 0:
            percentage_increase = ((current_avg - baseline_avg) / baseline_avg) * 100
            trend_score = max(0, percentage_increase) # Don't let it go negative
        else:
            # If baseline is 0, any traffic is a big signal
            trend_score = current_avg * 2 
        
        # D. Calculate Final Composite Score (70% Trends, 30% Social)
        composite_score = (trend_score * 0.7) + (social_score * 0.3)
        
        # E. Determine Threat Level & Action Item
        score = int(composite_score)
        if score > 80:
            level = "High"
            action = "ACTION: High threat detected. Recommend immediate public advisory and resource mobilization to hospitals."
        elif score > 50:
            level = "Elevated"
            action = "ALERT: Elevated search interest. Recommend alerting clinics and launching a preventative awareness campaign."
        elif score > 25:
            level = "Guarded"
            action = "WATCH: Search interest is above baseline. Monitor data daily and check pharmacy supplies."
        else:
            level = "Low"
            action = "INFO: Normal background chatter. No immediate action required."
            
        return score, level, action
        
    except Exception as e:
        print(f"!!! ERROR in calculate_threat_score: {e}")
        return 0, "Low", "Error in calculation logic."

# --- 7. The API Endpoint (for Person 2) ---
@app.route('/api/threat', methods=['GET'])
def get_threat_analysis():
    # Get parameters from URL (e.g., .../api/threat?disease=flu&city=delhi&geo=IN-DL)
    disease = request.args.get('disease', 'dengue')
    city = request.args.get('city', 'kanpur')
    geo = request.args.get('geo', 'IN-UP')
    
    print(f"\n[API] Received request: disease={disease}, city={city}, geo={geo}")
    
    # Validate disease
    if disease not in DISEASE_KEYWORDS:
        return jsonify({"error": "Disease not configured"}), 400
    disease_config = DISEASE_KEYWORDS[disease]
    
    # Fetch data from our functions
    trends_df, chart_data = get_google_trends(disease_config, geo)
    social_score = get_social_chatter(disease_config, city)
    
    # Calculate the score
    score, level, action = calculate_threat_score(trends_df, social_score, disease_config)
    
    # Build the final JSON response
    response_data = {
        'city': city.capitalize(),
        'disease': disease.capitalize(),
        'geo': geo,
        'threat_score': score,
        'threat_level': level,
        'action_item': action,
        'chart_data': chart_data, # This will be null if Google Trends fails
    }
    
    print(f"[API] Sending response: Threat Level = {level} (Score: {score})")
    
    return jsonify(response_data)

# --- 8. Run the App ---
if __name__ == '__main__':
    print("Starting Project Sentinel Backend...")
    print("Your frontend can now connect to http://<YOUR-IP-ADDRESS>:5001")
    # --- FINAL CHANGE ---
    # Listen on '0.0.0.0' to make the server accessible on your local network
    # Person 2 can connect using Person 1's IP address (e.g., http://192.168.1.10:5001)
    app.run(host='0.0.0.0', debug=True, port=5001)