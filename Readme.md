## Setup
Create a virtual environment 
```bash
python3 -m venv spotify_playlist_sort
cd spotify_playlist_sort
git clone ..
source bin/activate
cd ..
pip install -r requirements.txt
```

Then create your .env file inside the git repo

### Content 
```text
SPOTIPY_CLIENT_ID=''
SPOTIPY_CLIENT_SECRET=''
SPOTIPY_REDIRECT_URI=''
```
Find thoses data in your dashboard (need to create an app before)
https://developer.spotify.com/dashboard 
