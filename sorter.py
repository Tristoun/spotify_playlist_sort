import tkinter as tk
from tkinter import ttk, messagebox
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from os.path import join, dirname
from dotenv import load_dotenv
import threading

class SpotifySorterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Spotify Playlist Sorter")
        self.root.geometry("500x600")
        
        # Variables
        self.sp_client = None
        self.user_playlists_data = [] # To store full playlist objects
        
        # Load environment variables initially
        dotenv_path = join(dirname(__file__), '.env')
        load_dotenv(dotenv_path)

        self.setup_ui()

    def setup_ui(self):
        # --- Credentials Section ---
        cred_frame = ttk.LabelFrame(self.root, text="Step 1: Credentials", padding=10)
        cred_frame.pack(fill="x", padx=10, pady=10)

        # Client ID
        ttk.Label(cred_frame, text="Client ID:").grid(row=0, column=0, sticky="w")
        self.entry_id = ttk.Entry(cred_frame, width=40)
        self.entry_id.grid(row=0, column=1, padx=5, pady=2)
        if os.environ.get("SPOTIPY_CLIENT_ID"):
            self.entry_id.insert(0, os.environ.get("SPOTIPY_CLIENT_ID"))

        # Client Secret
        ttk.Label(cred_frame, text="Client Secret:").grid(row=1, column=0, sticky="w")
        self.entry_secret = ttk.Entry(cred_frame, show="*", width=40)
        self.entry_secret.grid(row=1, column=1, padx=5, pady=2)
        if os.environ.get("SPOTIPY_CLIENT_SECRET"):
            self.entry_secret.insert(0, os.environ.get("SPOTIPY_CLIENT_SECRET"))

        # Redirect URI
        ttk.Label(cred_frame, text="Redirect URI:").grid(row=2, column=0, sticky="w")
        self.entry_uri = ttk.Entry(cred_frame, width=40)
        self.entry_uri.grid(row=2, column=1, padx=5, pady=2)
        # Default or load from env
        uri_val = os.environ.get("SPOTIPY_REDIRECT_URI", "http://localhost:8888/callback")
        self.entry_uri.insert(0, uri_val)

        # Connect Button
        self.btn_connect = ttk.Button(cred_frame, text="Connect to Spotify", command=self.connect_spotify)
        self.btn_connect.grid(row=3, column=0, columnspan=2, pady=10)

        # --- Playlist Selection Section ---
        self.list_frame = ttk.LabelFrame(self.root, text="Step 2: Select Playlist", padding=10)
        self.list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.playlist_listbox = tk.Listbox(self.list_frame, selectmode=tk.SINGLE)
        self.playlist_listbox.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(self.list_frame, orient="vertical", command=self.playlist_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.playlist_listbox.config(yscrollcommand=scrollbar.set)

        # --- Action Section ---
        action_frame = ttk.Frame(self.root, padding=10)
        action_frame.pack(fill="x", padx=10, pady=5)

        self.status_label = ttk.Label(action_frame, text="Status: Waiting for connection...", foreground="gray")
        self.status_label.pack(side="top", pady=5)

        self.btn_sort = ttk.Button(action_frame, text="Sort Selected Playlist", command=self.start_sort_thread, state="disabled")
        self.btn_sort.pack(side="bottom", fill="x", pady=5)

    def connect_spotify(self):
        """Authenticates with Spotify using the inputs provided."""
        client_id = self.entry_id.get().strip()
        client_secret = self.entry_secret.get().strip()
        redirect_uri = self.entry_uri.get().strip()

        if not client_id or not client_secret or not redirect_uri:
            messagebox.showerror("Error", "Please fill in all credential fields.")
            return

        try:
            # We create the auth manager specifically with the inputs
            auth_manager = SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scope="playlist-modify-public playlist-modify-private playlist-read-private"
            )
            self.sp_client = spotipy.Spotify(auth_manager=auth_manager)
            
            # Test connection and fetch playlists
            self.status_label.config(text="Status: Connected! Fetching playlists...", foreground="green")
            self.root.update()
            self.fetch_playlists()
            
        except Exception as e:
            self.status_label.config(text="Status: Connection Failed", foreground="red")
            messagebox.showerror("Connection Error", str(e))

    def fetch_playlists(self):
        """Fetches current user's playlists and populates listbox."""
        try:
            results = self.sp_client.current_user_playlists()
            self.user_playlists_data = results['items']
            
            # Handle pagination for playlists if user has many
            while results['next']:
                results = self.sp_client.next(results)
                self.user_playlists_data.extend(results['items'])

            # Update GUI
            self.playlist_listbox.delete(0, tk.END)
            for item in self.user_playlists_data:
                self.playlist_listbox.insert(tk.END, item['name'])
            
            self.btn_sort.config(state="normal")
            self.status_label.config(text=f"Status: Found {len(self.user_playlists_data)} playlists.")

        except Exception as e:
            self.status_label.config(text="Status: Error fetching playlists", foreground="red")
            print(e)

    def start_sort_thread(self):
        """Starts the sorting logic in a separate thread to prevent freezing."""
        selection = self.playlist_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a playlist first.")
            return

        index = selection[0]
        target_playlist = self.user_playlists_data[index]
        
        # Disable button while working
        self.btn_sort.config(state="disabled", text="Sorting... Please Wait")
        
        # Run logic in thread
        thread = threading.Thread(target=self.sort_logic, args=(target_playlist,))
        thread.start()

    def sort_logic(self, target_playlist):
        """The core sorting algorithm from your original script."""
        try:
            self.update_status("Fetching tracks...", "blue")
            
            # 1. Get all tracks
            results = self.sp_client.playlist_tracks(target_playlist['uri'])
            tracks = results['items']
            while results['next']:
                results = self.sp_client.next(results)
                tracks.extend(results['items'])

            self.update_status(f"Processing {len(tracks)} tracks...", "blue")

            # 2. Group track URIs by user
            user_map = {}
            for item in tracks:
                # Some tracks might be local files or unavailable, causing errors if not checked
                if item['track'] and item['track']['uri']: 
                    user_id = item['added_by']['id']
                    track_uri = item['track']['uri']
                    
                    if user_id not in user_map:
                        user_map[user_id] = []
                    user_map[user_id].append(track_uri)

            # 3. Create Interleaved Order
            new_order_uris = []
            max_len = max(len(songs) for songs in user_map.values()) if user_map else 0
            users = list(user_map.keys())
            
            for i in range(max_len):
                for user in users:
                    if i < len(user_map[user]):
                        new_order_uris.append(user_map[user][i])

            # 4. Update Playlist
            self.update_status("Updating playlist on Spotify...", "blue")
            
            if new_order_uris:
                # Replace first 100
                self.sp_client.playlist_replace_items(target_playlist['id'], new_order_uris[:100])
                
                # Add the rest in chunks of 100
                if len(new_order_uris) > 100:
                    for i in range(100, len(new_order_uris), 100):
                        self.sp_client.playlist_add_items(target_playlist['id'], new_order_uris[i:i+100])
                
                self.update_status("Success! Playlist Sorted.", "green")
                messagebox.showinfo("Success", f"Playlist '{target_playlist['name']}' has been sorted!")
            else:
                self.update_status("No tracks found to sort.", "orange")

        except Exception as e:
            self.update_status("Error during sorting.", "red")
            messagebox.showerror("Error", str(e))
        finally:
            # Re-enable button (Must be done via thread-safe way or simply here since Tkinter tolerates this usually)
            self.root.after(0, lambda: self.btn_sort.config(state="normal", text="Sort Selected Playlist"))

    def update_status(self, text, color):
        self.root.after(0, lambda: self.status_label.config(text=f"Status: {text}", foreground=color))

if __name__ == "__main__":
    root = tk.Tk()
    app = SpotifySorterApp(root)
    root.mainloop()