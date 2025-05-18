# backend.py
import os
from flask import Flask, request, jsonify
from flask_cors import CORS # For handling Cross-Origin Resource Sharing
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app) # Enable CORS for all routes, allowing your frontend to call this backend

# Get Spotify API credentials from environment variables
# IMPORTANT: Create a .env file in the same directory as this script
# and add your Spotify API credentials like this:
# SPOTIPY_CLIENT_ID='YOUR_CLIENT_ID'
# SPOTIPY_CLIENT_SECRET='YOUR_CLIENT_SECRET'

CLIENT_ID = '66e7d064dbdc421d8a3b9b2faac6d408'
CLIENT_SECRET = 'ccd204ab13c84096b148b3c1091084a8'

# Check if credentials are set
if not CLIENT_ID or not CLIENT_SECRET:
    print("Error: SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET must be set as environment variables.")
    print("Create a .env file with these values.")
    # You might want to exit or raise an exception here in a real app
    # For now, we'll let it proceed, but Spotipy will fail.

# Initialize Spotipy with Client Credentials Flow
# This flow is suitable for backend services where you don't need user-specific data
# If you need user-specific data (like their private playlists), you'd use Authorization Code Flow
try:
    auth_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
    sp = spotipy.Spotify(auth_manager=auth_manager)
except Exception as e:
    print(f"Error initializing Spotipy: {e}")
    sp = None # Set sp to None if initialization fails

@app.route('/')
def home():
    """A simple route to check if the backend is running."""
    return "Spotify search backend is running!"

@app.route('/search', methods=['GET'])
def search_song():
    """
    Searches for a song on Spotify.
    Expects a 'song_name' query parameter.
    e.g., /search?song_name=Bohemian Rhapsody
    """
    if not sp:
        return jsonify({"error": "Spotipy not initialized. Check credentials."}), 500

    song_name = request.args.get('song_name')

    if not song_name:
        return jsonify({"error": "Missing 'song_name' query parameter"}), 400

    try:
        # Perform the search using Spotipy
        results = sp.search(q=song_name, type='track', limit=10) # Get up to 10 tracks
        items = results.get('tracks', {}).get('items', [])

        if items:
            # Format the tracks to send back to the frontend
            formatted_tracks = []
            for track in items:
                formatted_tracks.append({
                    "name": track.get('name'),
                    "artists": [artist.get('name') for artist in track.get('artists', [])],
                    "album": track.get('album', {}).get('name'),
                    "uri": track.get('uri'),
                    "external_urls": track.get('external_urls', {}).get('spotify'),
                    "cover_image": track.get('album', {}).get('images', [{}])[0].get('url')  # Get first image (usually largest)
                })
            return jsonify({"tracks": formatted_tracks})
        else:
            return jsonify({"message": f"No tracks found matching '{song_name}'."})

    except spotipy.exceptions.SpotifyException as e:
        # Handle Spotify API specific errors
        return jsonify({"error": f"Spotify API error: {str(e)}"}), 500
    except Exception as e:
        # Handle other potential errors
        app.logger.error(f"An unexpected error occurred: {e}") # Log the error
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


if __name__ == '__main__':
    # Run the Flask app
    # Debug mode should be False in a production environment like Koyeb.
    # Koyeb will set the PORT environment variable, which Flask can use.
    # Binding to '0.0.0.0' is crucial for the app to be reachable in a container.
    port = int(os.environ.get('PORT', 8000)) # Use Koyeb's PORT or default to 8000
    # For production on Koyeb, debug should ideally be False.
    # You can control debug mode via an environment variable if needed.
    # DEBUG_MODE = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=True) # Set debug=False for production
    # The app will be accessible at http://0.0.0.0:PORT/ within the container
    # and through Koyeb's public URL.
