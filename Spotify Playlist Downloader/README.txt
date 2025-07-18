Getting Your Spotify Credentials & Playlist URI

#### 1. Create a Spotify App
Head to https://developer.spotify.com/dashboard and log in.

Click the green "Create App" button.

For App Name and App Description, you can enter anything (e.g., `"Testing"`).

Check both agreement boxes and click "Create".

#### 2. Get Your Client ID & Client Secret
Once your app is created, you'll see a Client ID on the left. Copy and save it. You’ll need it later.

Click "Show client secret" to reveal your Client Secret. Copy and save that as well.

#### 3. Find Your Playlist URI
Open Spotify and locate the playlist you want to download.

Right-click the playlist, hover over "Share", and select "Copy Spotify URI".

The URI will look something like:  
  https://open.spotify.com/playlist/38Ff1xR9Pw4kZ2yW0KiHHY?si=IF29XUDsT9qGIKqXWzOpGQ

For use in scripts, only copy the part after `/playlist/`  

In this case, you'd use: `38Ff1xR9Pw4kZ2yW0KiHHY?si=IF29XUDsT9qGIKqXWzOpGQ`
Save this URI somewhere accessible.

