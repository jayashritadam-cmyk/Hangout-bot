# Highrise Music Bot (Python)

A simple Highrise bot framework using the Highrise Python SDK.

## Setup Instructions

1.  **Install Requirements:**
    Open your terminal in this directory and run:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configure Environment:**
    Open the `.env` file and replace `YOUR_ROOM_ID_HERE` and `YOUR_API_TOKEN_HERE` with your actual room ID and API token from the [Highrise Create Portal](https://create.highrise.game/).

3.  **Run the Bot:**
    Use the `highrise-bot` CLI to launch your bot:
    ```bash
    highrise-bot -t <YOUR_API_TOKEN> -r <YOUR_ROOM_ID> main:MusicBot
    ```
    Alternatively, if your CLI supports environment loading:
    ```bash
    highrise-bot -t $(grep API_TOKEN .env | cut -d '=' -f2) -r $(grep ROOM_ID .env | cut -d '=' -f2) main:MusicBot
    ```

## Features
-   **Welcome Message:** Greets users when they join the room.
-   **!ping Command:** Simple test command for availability.
-   **!help Command:** Lists available commands.

## Customization
You can modify `main.py`'s `MusicBot` class to add more features like:
-   Playing emotes based on chat commands.
-   Moving to specific positions.
-   Handling room ownership tasks.
