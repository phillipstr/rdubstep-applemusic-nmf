import csv
import os
import time
from datetime import datetime
import spotipy
import applemusicpy
from spotipy.oauth2 import SpotifyClientCredentials

# --- CONFIG ---
SPOTIFY_CLIENT_ID = os.environ["SPOTIFY_CLIENT_ID"]
SPOTIFY_CLIENT_SECRET = os.environ["SPOTIFY_CLIENT_SECRET"]
SPOTIFY_PLAYLIST_ID = os.environ.get("SPOTIFY_PLAYLIST_ID", "18ePsc36VbfsskyTBHpGZN")

APPLE_KEY_ID = os.environ["APPLE_KEY_ID"]
APPLE_TEAM_ID = os.environ["APPLE_TEAM_ID"]
APPLE_PRIVATE_KEY = os.environ["APPLE_PRIVATE_KEY"]  # Contents of .p8 file
APPLE_MUSIC_USER_TOKEN = os.environ["APPLE_MUSIC_USER_TOKEN"]
APPLE_PLAYLIST_ID = os.environ.get("APPLE_PLAYLIST_ID", "pl.u-NpXmza4Cm6xAyp6")


# --- STEP 1: Fetch Spotify tracks ---
def get_spotify_tracks(playlist_id: str) -> list[dict]:
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
    ))

    tracks = []
    results = sp.playlist_tracks(playlist_id)
    while results:
        for item in results["items"]:
            track = item.get("track")
            if track:
                tracks.append({
                    "name": track["name"],
                    "artist": track["artists"][0]["name"],
                    "album": track["album"]["name"],
                })
        results = sp.next(results) if results["next"] else None

    print(f"Found {len(tracks)} tracks on Spotify.")
    return tracks


# --- STEP 2: Search Apple Music for each track ---
def search_apple_music(am: applemusicpy.AppleMusic, track: dict) -> str | None:
    query = f"{track['name']} {track['artist']}"
    results = am.search(query, types=["songs"], limit=1)
    songs = results.get("songs", {}).get("data", [])
    if songs:
        return songs[0]["id"]
    print(f"  ⚠️  Not found on Apple Music: {track['name']} — {track['artist']}")
    return None


# --- STEP 2b: Write unmatched tracks to a CSV artifact ---
def write_unmatched_report(unmatched: list[dict]) -> str | None:
    if not unmatched:
        print("All tracks matched — no unmatched report needed.")
        return None

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"unmatched_tracks_{timestamp}.csv"

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "artist", "album"])
        writer.writeheader()
        writer.writerows(unmatched)

    print(f"📄 Unmatched tracks written to {filename} ({len(unmatched)} songs).")
    return filename


# --- STEP 3: Clear existing Apple Music playlist ---
def clear_playlist(am: applemusicpy.AppleMusic, playlist_id: str):
    response = am.get(f"me/library/playlists/{playlist_id}/tracks")
    track_ids = [t["id"] for t in response.get("data", [])]

    # Handle pagination
    while response.get("next"):
        response = am.get(response["next"])
        track_ids += [t["id"] for t in response.get("data", [])]

    if not track_ids:
        print("Playlist is already empty.")
        return

    am.delete(
        f"me/library/playlists/{playlist_id}/tracks",
        {"data": [{"id": tid, "type": "library-songs"} for tid in track_ids]}
    )
    print(f"Cleared {len(track_ids)} tracks from existing playlist.")


# --- STEP 4: Add new tracks to Apple Music playlist ---
def add_tracks_to_playlist(am: applemusicpy.AppleMusic, playlist_id: str, track_ids: list[str]):
    payload = {"data": [{"id": tid, "type": "songs"} for tid in track_ids]}
    am.post(f"me/library/playlists/{playlist_id}/tracks", payload)
    print(f"✅ Added {len(track_ids)} tracks to playlist.")


# --- MAIN ---
def main():
    print("=== Spotify → Apple Music Sync ===\n")

    # Init Apple Music client
    am = applemusicpy.AppleMusic(
        secret_key=APPLE_PRIVATE_KEY,
        key_id=APPLE_KEY_ID,
        team_id=APPLE_TEAM_ID,
        music_user_token=APPLE_MUSIC_USER_TOKEN
    )

    # Fetch tracks from Spotify
    spotify_tracks = get_spotify_tracks(SPOTIFY_PLAYLIST_ID)

    # Search each track on Apple Music
    apple_track_ids = []
    unmatched_tracks = []
    for track in spotify_tracks:
        apple_id = search_apple_music(am, track)
        if apple_id:
            apple_track_ids.append(apple_id)
        else:
            unmatched_tracks.append(track)
        time.sleep(0.1)  # Avoid hammering the API

    print(f"\nMatched {len(apple_track_ids)}/{len(spotify_tracks)} tracks on Apple Music.")

    # Write unmatched tracks to CSV artifact
    write_unmatched_report(unmatched_tracks)

    if not apple_track_ids:
        print("No tracks matched — aborting sync.")
        return

    # Clear existing playlist and add new tracks
    print(f"\nClearing Apple Music playlist {APPLE_PLAYLIST_ID}...")
    clear_playlist(am, APPLE_PLAYLIST_ID)

    print("Adding matched tracks...")
    add_tracks_to_playlist(am, APPLE_PLAYLIST_ID, apple_track_ids)

    print("\n✅ Sync complete.")


if __name__ == "__main__":
    main()
