import requests
import pandas as pd
import time

# Hardcoded API Key
api_key = "d3e8d7fcb94be031986259192b4fdfb0"

# Base URLs
base_url = "https://api.themoviedb.org/3"
url = f"{base_url}/movie/popular"
credits_url_template = f"{base_url}/movie/{{}}/credits"
providers_url_template = f"{base_url}/movie/{{}}/watch/providers"
reviews_url_template = f"{base_url}/movie/{{}}/reviews"

total_pages = 100
all_movies = []

# Use requests.Session() for efficiency
session = requests.Session()

# Track seen usernames globally
global_seen_users = set()

def fetch_data(url):
    """Helper function to handle API requests with error handling."""
    try:
        response = session.get(url, params={"api_key": api_key})
        response.raise_for_status()  # Raise HTTPError for bad responses
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

for page in range(1, total_pages + 1):
    data = fetch_data(f"{url}?page={page}")
    
    if data and "results" in data:
        movies = data["results"]
        
        for movie in movies:
            movie_id = movie["id"]
            
            # Get cast names
            credits_data = fetch_data(credits_url_template.format(movie_id))
            if credits_data:
                cast_names = {cast["name"] for cast in credits_data.get("cast", [])}
                movie["cast_names"] = ", ".join(cast_names)
            else:
                movie["cast_names"] = None
            
            # Get watch providers
            providers_data = fetch_data(providers_url_template.format(movie_id))
            if providers_data:
                provider_names = set()  
                for region, provider_info in providers_data.get("results", {}).items():
                    for category, providers_list in provider_info.items():
                        if isinstance(providers_list, list):
                            provider_names.update(provider["provider_name"] for provider in providers_list)
                movie["watch_providers"] = ", ".join(provider_names)
            else:
                movie["watch_providers"] = None
            
            # Get first globally unique user_name with a rating, fallback to first available rating
            reviews_data = fetch_data(reviews_url_template.format(movie_id))
            movie["user_name"], movie["user_rating"] = None, None  # Default to None
            
            local_seen_users = set()  # Track unique usernames within the movie
            fallback_user = None
            fallback_rating = None
            
            if reviews_data and "results" in reviews_data:
                for review in reviews_data["results"]:
                    author_details = review.get("author_details", {})
                    user_name = author_details.get("name")
                    rating = author_details.get("rating")
                    
                    if user_name and rating is not None:
                        if user_name not in global_seen_users:
                            movie["user_name"] = user_name
                            movie["user_rating"] = rating
                            global_seen_users.add(user_name)
                            break  # Stop once we find a globally unique user
                        
                        if not fallback_user:  # Store the first valid rating as a fallback
                            fallback_user = user_name
                            fallback_rating = rating
                        
                    local_seen_users.add(user_name)
            
            if movie["user_name"] is None and fallback_user:  # Use fallback if no unique user found
                movie["user_name"] = fallback_user
                movie["user_rating"] = fallback_rating
            
            time.sleep(0.2)  # Short delay to avoid rate limiting
        
        all_movies.extend(movies)
    else:
        print(f"Error retrieving page {page}, skipping...")
    
    time.sleep(0.5)

# Convert to DataFrame
movies_df = pd.DataFrame(all_movies)


