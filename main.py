import asyncio
import os
import json
import traceback
import urllib.parse
import aiohttp
import random
import time
from dotenv import load_dotenv
from highrise import BaseBot
from highrise.models import SessionMetadata, ChatEvent, User, Position, AnchorPosition, Error, RoomPermissions, UserMovedEvent, Item

# Load environment variables (optional if using config.json)
load_dotenv()

class MusicBot(BaseBot):
    def __init__(self):
        super().__init__()
        self.config_path = "config.json"
        self.load_config()
        self.is_locked = False
        self.is_looping = True
        self.is_running = True
        self.floss_emotes = ["dance-floss"]
        self.flash_users = set()
        self.user_loops = {} # Track active loops for users
        self.all_emotes = {} # Full emote list
        self.id_cache = {} # Cache for username -> user_id to speed up invites
        self.original_outfit = None # Store bot's starting outfit
        self.session = None # aiohttp session for Web API
        self.frozen_users = {} # {user_id: position}
        self.banned_users = {} # {username: user_id}
        self.welcome_messages = [
            "Welcome to the room @{user}! 🌟",
            "Hey @{user}, glad you could make it! 👋",
            "Yo @{user}! Grab a seat and enjoy. 🍿",
            "Welcome home @{user}! 🏠✨",
            "Look who it is! Welcome @{user}! 🌈",
            "Ayyy @{user} is in the house! 🥳",
            "Welcome @{user}! Stay a while. ☕",
            "Nice to see you @{user}! 😊",
            "Welcome @{user}! Let's vibe! 🎶",
            "Glad you're here @{user}! ✨",
            "Welcome @{user}! Hope you're having a great day! ☀️",
            "Hello @{user}! Welcome to our little corner. 🍃",
            "Welcome @{user}! Make yourself at home. 🛋️",
            "Hey @{user}! Great to see a new face! 👋",
            "Welcome @{user}! The party's just starting! 🎊",
            "Yo @{user}! Ready to hang out? 😎",
            "Welcome @{user}! Don't be shy, say hi! 👋",
            "Hi @{user}! Welcome to the squad. 💎",
            "Welcome @{user}! You've joined the coolest room. 😎",
            "Hey @{user}! Let's make some memories. ✨",
            "Welcome @{user}! Stay awesome. 🌟",
            "Yo @{user}! Welcome to the vibe zone. 🌀",
            "Welcome @{user}! Feel the rhythm. 🎵",
            "Welcome @{user}! Join the fun! 🎈",
            "Hey @{user}! Glad you're part of the team today. 🤝",
            "Welcome @{user}! Enjoy the music and the mood. 🎷",
            "Yo @{user}! Welcome to the top tier. 🏆",
            "Welcome @{user}! Let's get this party rolling. 🚗",
            "Hey @{user}! Welcome to the family. ❤️",
            "Welcome @{user}! Check out the view. 🏔️",
            "Yo @{user}! Welcome to the chill spot. ❄️",
            "Welcome @{user}! The energy just went up! ⚡",
            "Hey @{user}! Welcome to the spotlight. 🔦",
            "Welcome @{user}! Let's create something cool. 🎨",
            "Yo @{user}! Welcome to the adventure. 🗺️",
            "Welcome @{user}! Glad you found us. 🔍",
            "Hey @{user}! Welcome to the future. 🚀",
            "Welcome @{user}! Let's stay positive. ✨",
            "Yo @{user}! Welcome to the dream world. 💭",
            "Welcome @{user}! You're just in time. ⏳",
            "Hey @{user}! Welcome to the magic. 🪄",
            "Welcome @{user}! Let's spark some joy. ✨",
            "Yo @{user}! Welcome to the harmony. 🎹",
            "Welcome @{user}! Let's make it legendary. ⚔️",
            "Hey @{user}! Welcome to the oasis. 🌴",
            "Welcome @{user}! Let's ride the wave. 🌊",
            "Yo @{user}! Welcome to the summit. ⛰️",
            "Welcome @{user}! Let's shine together. ✨",
            "Hey @{user}! Welcome to the galaxy. 🌌",
            "Welcome @{user}! You're the missing piece. 🧩"
        ]
        self.vip_welcome_messages = [
            "👑 MASSIVE WELCOME BACK TO OUR VIP @{user}! 👑",
            "✨ A true legend has entered! Welcome @{user}! ✨",
            "🌟 Make way for our VIP member, @{user}! 🌟",
            "💎 The high roller @{user} is here! Welcome! 💎",
            "🔥 THE MVP IS HERE! Welcome back @{user}! 🔥",
            "🌈 Our favorite VIP @{user} just joined the party! 🌈",
            "🏆 A champion enters the room! Welcome @{user}! 🏆",
            "⚡ The room just got 10x brighter! Welcome VIP @{user}! ⚡",
            "🛸 Welcome back to your kingdom, @{user}! 👾",
            "🌹 Sending extra love to our VIP @{user}! Welcome! 🌹",
            "🚀 To the moon! Our VIP @{user} has arrived! 🚀",
            "🎊 Celebration time! VIP @{user} is here! 🎊",
            "💥 BOOM! The one and only @{user} has joined! 💥",
            "🎸 Rock star @{user} in the building! Welcome! 🎸",
            "🥂 Cheers to our amazing VIP, @{user}! 🥂",
            "🛡️ The elite @{user} has entered the chat! 🛡️",
            "🎭 Welcome to the show, VIP @{user}! 🎭",
            "🏰 Welcome back to your castle, @{user}! 🏰",
            "💫 Shine bright like a diamond, @{user}! Welcome VIP! 💫",
            "🌋 THE GOAT @{user} HAS ARRIVED! 🌋"
        ]
        self.owner_welcome_messages = [
            "👑 ALL HAIL THE CREATOR @{user}! 👑",
            "⚡ THE LEGENDARY OWNER @{user} IS HERE! ⚡",
            "🏰 Welcome back to your throne, @{user}! 🏰",
            "🔥 THE BOSS @{user} HAS ARRIVED! 🔥",
            "✨ The room is now complete! Welcome Owner @{user}! ✨",
            "🌟 A god among men! Welcome @{user}! 🌟",
            "🛡️ The guardian of this world, @{user}! 🛡️",
            "🚀 The captain @{user} is on deck! 🚀",
            "💎 The highest rank has entered: @{user}! 💎",
            "🌋 THE ULTIMATE POWER @{user} IS HERE! 🌋"
        ]
        self.mod_welcome_messages = [
            "👮 MODERATOR ON DUTY: Welcome @{user}! 👮",
            "⚔️ The enforcer @{user} has joined! ⚔️",
            "🛡️ Welcome back, Protector @{user}! 🛡️",
            "⚡ Safety first! Welcome Mod @{user}! ⚡",
            "🔥 RESPECT! Our Moderator @{user} is here! 🔥",
            "⚖️ The scales of justice arrive: @{user}! ⚖️",
            "📢 Attention! Mod @{user} has entered! 📢",
            "💎 Our trusted Moderator @{user} is online! 💎",
            "🚀 Clear the way for Mod @{user}! 🚀",
            "✨ Glad to have you here, Mod @{user}! ✨"
        ]
        self.load_floss_emotes()
        self.load_all_emotes_json()

    def load_floss_emotes(self):
        try:
            with open("emote_list_backup.json", "r") as f:
                emotes_data = json.load(f)
                # Filter for any emote that has "floss" in its key or value (id)
                for key, data in emotes_data.items():
                    if isinstance(data, dict) and "id" in data:
                        if "floss" in key.lower() or "floss" in data["id"].lower():
                            if data["id"] not in self.floss_emotes:
                                self.floss_emotes.append(data["id"])
            print(f"Loaded floss emotes: {self.floss_emotes}")
        except Exception as e:
            print(f"Error loading floss emotes from JSON: {e}")

    def load_all_emotes_json(self):
        try:
            with open("emote_list_backup.json", "r") as f:
                self.all_emotes = json.load(f)
            print(f"Loaded {len(self.all_emotes)} emotes for user loops.")
        except Exception as e:
            print(f"Error loading all emotes from JSON: {e}")

    def load_config(self):
        try:
            with open(self.config_path, "r") as f:
                self.config = json.load(f)
                # Support both old OWNER (string) and new OWNERS (list)
                if "OWNER" in self.config and "OWNERS" not in self.config:
                    self.owners = [self.config["OWNER"]]
                else:
                    self.owners = self.config.get("OWNERS", ["_inferno__"])
                
                self.saved_pos = self.config.get("SAVED_POSITION")
                self.subscribers = self.config.get("SUBSCRIBERS", [])
                self.vips = self.config.get("VIPS", [])
                self.mods = self.config.get("MODERATORS", [])
                self.room_id = self.config.get("ROOM_ID")
                self.tele_locations = self.config.get("TELEPORT_LOCATIONS", {})
        except:
            self.owners = ["_inferno__"]
            self.saved_pos = None
            self.subscribers = []
            self.vips = []
            self.mods = []
            self.room_id = None
            self.tele_locations = {}

    def save_config(self):
        try:
            self.config["OWNERS"] = self.owners
            self.config["SUBSCRIBERS"] = self.subscribers
            self.config["VIPS"] = self.vips
            self.config["MODERATORS"] = self.mods
            self.config["TELEPORT_LOCATIONS"] = self.tele_locations
            with open(self.config_path, "w") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")



    def is_vip(self, username):
        return username.lower() in [v.lower() for v in self.vips]

    def is_owner(self, username):
        return username.lower() in [o.lower() for o in self.owners]

    def is_mod(self, username):
        return username.lower() in [m.lower() for m in self.mods]

    def is_subscribed(self, username):
        return self.is_owner(username) or self.is_mod(username) or self.is_vip(username) or username.lower() in [s.lower() for s in self.subscribers]

    async def is_mod_or_owner(self, user_id, username):
        if self.is_owner(username):
            return True
        if username.lower() in [m.lower() for m in self.mods]:
            return True
        try:
            privs = await self.highrise.get_room_privilege(user_id)
            if not isinstance(privs, Error):
                return privs.moderator is True
        except Exception as e:
            print(f"Error checking privileges: {e}")
        return False

    async def run_emote_loop(self):
        """Continuously loop the floss emotes."""
        while self.is_running:
            try:
                if self.is_looping:
                    for emote_id in self.floss_emotes:
                        if not self.is_looping:
                            break
                        try:
                            await self.highrise.send_emote(emote_id)
                        except Exception as e:
                            if "User not in room" not in str(e):
                                print(f"Error sending emote {emote_id}: {e}")
                        # Wait for the emote to finish or a reasonable interval
                        await asyncio.sleep(10)
                else:
                    await asyncio.sleep(5)  # Wait while loop is paused
            except Exception as e:
                if not self.is_running:
                    break
                if "User not in room" not in str(e):
                    print(f"Error in emote loop: {e}")
                await asyncio.sleep(5)  # Wait before retrying

    def get_gold_bar_id(self, amount: str):
        mapping = {
            "1": "gold_bar_1",
            "5": "gold_bar_5",
            "10": "gold_bar_10",
            "50": "gold_bar_50",
            "100": "gold_bar_100",
            "500": "gold_bar_500",
            "1k": "gold_bar_1k",
            "1000": "gold_bar_1k",
            "5k": "gold_bar_5000",
            "5000": "gold_bar_5000",
            "10k": "gold_bar_10k",
            "10000": "gold_bar_10k",
        }
        return mapping.get(amount.lower())

    async def get_bot_gold(self):
        try:
            wallet = await self.highrise.get_wallet()
            if isinstance(wallet, Error):
                return 0
            for item in wallet.content:
                if item.type == "gold":
                    return item.amount
            return 0
        except Exception as e:
            print(f"Error fetching gold: {e}")
            return 0

    async def _get_session(self):
        """Unified internal method to manage the aiohttp session with double-check lock."""
        if not hasattr(self, "_session_lock"):
            self._session_lock = asyncio.Lock()
            
        async with self._session_lock:
            if self.session is None or self.session.closed:
                self.session = aiohttp.ClientSession()
        return self.session

    async def get_id_from_name(self, username):

        try:
            room_users = await self.highrise.get_room_users()
            if isinstance(room_users, Error):
                return None
            for user, pos in room_users.content:
                if user.username.lower() == username.lower():
                    return user.id
            
            # If not in room, try Highrise Web API
            return await self.get_user_id_webapi(username)
        except Exception as e:
            print(f"Error getting ID from name: {e}")
            return None

    async def get_user_id_webapi(self, username):
        """Ultra-robust user ID lookup with multi-strategy resolution."""
        clean_name = str(username).replace("@", "").strip()
        name_lower = clean_name.lower()
        
        if name_lower in self.id_cache:
            return self.id_cache[name_lower]

        try:
            session = await self._get_session()
            
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "Highrise/3.16.0 (iPhone; iOS 17.1; Scale/3.00)",
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1"
            ]

            quoted_name = urllib.parse.quote(clean_name)
            
            # Strategy 1: Direct Profile Fetch (Try multiple API versions)
            for ua in user_agents:
                headers = {"User-Agent": ua, "Accept": "application/json"}
                for url in [
                    f"https://webapi.highrise.game/v1/users/{quoted_name}",
                    f"https://webapi.highrise.game/users/{quoted_name}"
                ]:
                    async with session.get(url, headers=headers, timeout=10) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            uid = data.get("user", {}).get("user_id") or data.get("user_id")
                            if uid:
                                self.id_cache[name_lower] = uid
                                print(f"DEBUG: Resolved ID for {clean_name} via Direct Profile ({url}): {uid}")
                                return uid
                        elif resp.status == 404: continue # Try next URL

            # Strategy 2: Search API
            for ua in user_agents:
                headers = {"User-Agent": ua, "Accept": "application/json"}
                for search_url in [
                    f"https://webapi.highrise.game/v1/users?username={quoted_name}&limit=5",
                    f"https://webapi.highrise.game/users?username={quoted_name}&limit=5"
                ]:
                    async with session.get(search_url, headers=headers, timeout=10) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if isinstance(data, dict) and data.get("users"):
                                for u in data["users"]:
                                    if u.get("username", "").lower() == name_lower:
                                        uid = u.get("user_id")
                                        self.id_cache[name_lower] = uid
                                        print(f"DEBUG: Found ID for {clean_name} via Search ({search_url}): {uid}")
                                        return uid

            return None
        except Exception as e:
            print(f"CRITICAL Search Failure for {clean_name}: {e}")
            return None


    async def process_subscriber_invites(self, requester: User):
        """Ultra-robust invitation process with caching and error reporting."""
        try:
            if not self.subscribers:
                await self.highrise.chat("Subscription list is empty! Add users with -sub @username first.")
                return

            target_usernames = list(set([s.lower() for s in self.subscribers]))
            total_targets = len(target_usernames)
            
            await self.highrise.chat(f"📢 Invite Broadcast: Sending invitations to ALL {total_targets} subscribers... ⏳")

            # 1. Quick Refresh ID Map from current room
            room_users_res = await self.highrise.get_room_users()
            in_room_map = {}
            if not isinstance(room_users_res, Error):
                for u, pos in room_users_res.content:
                    in_room_map[u.username.lower()] = u.id
                    self.id_cache[u.username.lower()] = u.id # Update cache while we're at it

            # 2. Sequential ID Retrieval (Prioritizing Cache)
            user_ids = []
            failed_usernames = []
            
            for username in target_usernames:
                uid = in_room_map.get(username) or self.id_cache.get(username)
                
                if not uid:
                    # Still not found, hit the Web API
                    uid = await self.get_user_id_webapi(username)
                    if uid:
                        await asyncio.sleep(0.15) # Safety throttle
                
                if uid:
                    user_ids.append(uid)
                else:
                    failed_usernames.append(username)

            if not user_ids:
                await self.highrise.chat("❌ Critical: Could not find ANY valid IDs from the subscriber list!")
                return

            # 3. Batch Sending (Max 100 per call)
            sent_count = 0
            for i in range(0, len(user_ids), 100):
                batch = user_ids[i:i+100]
                await self.highrise.send_message_bulk(batch, f"Our room is live! Join the party now! ✨🔊", message_type="invite", room_id=self.room_id)
                sent_count += len(batch)
                if i + 100 < len(user_ids):
                    await asyncio.sleep(1.0) 

            # 4. Final Advanced Summary
            success_msg = f"✅ Broadcast Complete! ({sent_count}/{total_targets} sent)"
            if failed_usernames:
                success_msg += f"\n⚠️ Missing IDs for: {', '.join(failed_usernames[:5])}"
                if len(failed_usernames) > 5:
                    success_msg += " ..."
            
            await self.highrise.chat(success_msg)
                                     
        except Exception as e:
            print(f"Error in process_subscriber_invites: {e}")
            await self.highrise.chat(f"❌ Broadcast process failed: {type(e).__name__}")

    async def get_user_outfit_webapi(self, target):
        """Ultra-robust, multi-strategy fix for global outfit retrieval."""
        if not target: return None
        target_clean = str(target).replace("@", "").strip()
        
        try:
            session = await self._get_session()
            
            # Diverse User-Agents to bypass restrictions
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "Highrise/3.16.0 (iPhone; iOS 17.1; Scale/3.00)",
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1"
            ]
            
            async def fetch_json(url, ua):
                try:
                    headers = {"User-Agent": ua, "Accept": "application/json", "Accept-Language": "en-US,en;q=0.9"}
                    async with session.get(url, headers=headers, timeout=10) as resp:
                        if resp.status == 200:
                            return await resp.json()
                        elif resp.status == 404: return "NOT_FOUND"
                except: return None
                return None

            def parse_items(data):
                if not data: return None
                outfit = None
                if isinstance(data, list): outfit = data
                elif isinstance(data, dict):
                    # Multi-layer extraction to handle all known API response formats
                    outfit = (data.get("outfit") or 
                             data.get("user", {}).get("outfit") or 
                             data.get("content", {}).get("outfit") or
                             data.get("data", {}).get("outfit"))
                    
                    # If it's still a dict, it might be the "category: item" format
                    if isinstance(outfit, dict):
                        # Some endpoints return { "category": { "id": "...", "amount": 1 } }
                        extracted_list = []
                        for key, val in outfit.items():
                            if isinstance(val, dict) and "id" in val:
                                extracted_list.append(val)
                            elif isinstance(val, str):
                                extracted_list.append({"id": val, "amount": 1})
                        outfit = extracted_list if extracted_list else None
                
                if outfit and isinstance(outfit, list):
                    items = []
                    for i in outfit:
                        if isinstance(i, dict) and "id" in i:
                            items.append(Item(type='clothing', id=i["id"], amount=i.get("amount", 1)))
                        elif isinstance(i, str): # Handle simple ID lists if they exist
                            items.append(Item(type='clothing', id=i, amount=1))
                    return items if items else None
                return None

            # Strategy 1: Immediate Direct Name-to-Outfit Fetch
            quoted_name = urllib.parse.quote(target_clean)
            for ua in user_agents:
                for url in [
                    f"https://webapi.highrise.game/v1/users/{quoted_name}/outfit",
                    f"https://webapi.highrise.game/users/{quoted_name}/outfit"
                ]:
                    data = await fetch_json(url, ua)
                    if data == "NOT_FOUND": continue
                    items = parse_items(data)
                    if items: return items

            # Strategy 2: ID Resolution via Search (if not a hex ID)
            resolved_id = None
            is_hex_id = len(target_clean) == 24 and all(c in "0123456789abcdef" for c in target_clean.lower())
            
            if not is_hex_id:
                resolved_id = await self.get_user_id_webapi(target_clean)
            
            id_to_use = resolved_id or target_clean
            
            # Strategy 3: Exhaustive endpoint search with the best ID found
            for ua in user_agents:
                for url_template in [
                    f"https://webapi.highrise.game/v1/users/{id_to_use}/outfit",
                    f"https://webapi.highrise.game/users/{id_to_use}/outfit",
                    f"https://webapi.highrise.game/v1/users/{id_to_use}",
                    f"https://webapi.highrise.game/users/{id_to_use}",
                    f"https://webapi.highrise.game/v1/user/{id_to_use}/profile",
                    f"https://webapi.highrise.game/user/{id_to_use}/profile"
                ]:
                    data = await fetch_json(url_template, ua)
                    if data == "NOT_FOUND": continue
                    items = parse_items(data)
                    if items: return items
                    
            return None
        except Exception as e:
            print(f"DEBUG: WebAPI Outfit Retrieval Error: {e}")
            return None






    async def on_start(self, session_metadata: SessionMetadata) -> None:
        """Called when the bot starts."""
        try:
            self.my_id = session_metadata.user_id
            print(f"Bot successfully started in room connection!")
            print(f"Bot ID: {self.my_id}")
            
            # Initialize aiohttp session for Web API
            await self._get_session()
            
            # Save original outfit for -revertfit
            if "ORIGINAL_OUTFIT" in self.config:
                # Load from config if it exists
                try:
                    self.original_outfit = [Item(type='clothing', id=i["id"], amount=i.get("amount", 1)) for i in self.config["ORIGINAL_OUTFIT"]]
                    print("Original outfit loaded from config!")
                except Exception as e:
                    print(f"Error loading original outfit from config: {e}")
                    self.original_outfit = None

            if not self.original_outfit:
                try:
                    outfit_res = await self.highrise.get_user_outfit(self.my_id)
                    if not isinstance(outfit_res, Error):
                        self.original_outfit = outfit_res.outfit
                        # Save to config for future sessions
                        self.config["ORIGINAL_OUTFIT"] = [{"id": i.id, "amount": i.amount} for i in self.original_outfit]
                        self.save_config()
                        print("Original outfit saved and persisted!")
                except Exception as e:
                    print(f"Failed to save original outfit: {e}")
            
            # Start the emote loop in the background
            asyncio.create_task(self.run_emote_loop())
            
            # Start the advertisement loop in the background (every 7 minutes)
            asyncio.create_task(self.run_advertisement_loop())
            
            # Move to saved position if it exists
            if self.saved_pos:
                try:
                    pos = Position(
                        x=self.saved_pos['x'],
                        y=self.saved_pos['y'],
                        z=self.saved_pos['z'],
                        facing=self.saved_pos.get('facing', 'FrontRight')
                    )
                    await self.highrise.walk_to(pos)
                    print(f"Moved to saved position: {pos}")
                except Exception as e:
                    print(f"Error moving to saved position: {e}")



            await self.highrise.chat("Bot is now online! type -help to see commands.")
        except BaseException as e:
            print(f"ERROR in on_start: {type(e).__name__}: {e}")
            traceback.print_exc()

    async def on_stop(self) -> None:
        """Called when the bot stops."""
        self.is_running = False
        if self.session and not self.session.closed:
            try:
                await self.session.close()
                print("aiohttp session closed successfully.")
            except Exception as e:
                print(f"Error while closing session: {e}")
        print("Bot stopped.")

    async def on_user_join(self, user: User, position: Position | AnchorPosition) -> None:
        """Called when a user joins the room."""
        try:
            print(f"User {user.username} joined.")


            # Randomly select a welcome message
            if self.is_owner(user.username):
                welcome_msg = random.choice(self.owner_welcome_messages).format(user=user.username)
            elif self.is_mod(user.username):
                welcome_msg = random.choice(self.mod_welcome_messages).format(user=user.username)
            elif self.is_subscribed(user.username): # is_subscribed already checks VIPs/Subscribers
                welcome_msg = random.choice(self.vip_welcome_messages).format(user=user.username)
            else:
                welcome_msg = random.choice(self.welcome_messages).format(user=user.username)
            await self.highrise.chat(welcome_msg)
        except BaseException as e:
            print(f"ERROR in on_user_join: {type(e).__name__}: {e}")
            traceback.print_exc()

    async def on_user_leave(self, user: User) -> None:
        """Called when a user leaves the room."""
        try:
            print(f"User {user.username} left.")

        except Exception as e:
            print(f"Error in on_user_leave: {e}")

    async def on_user_move(self, user: User, destination: Position | AnchorPosition) -> None:
        """Called when a user moves in the room."""
        try:
            # Enforce freeze
            if user.id in self.frozen_users:
                freeze_pos = self.frozen_users[user.id]
                if isinstance(freeze_pos, Position):
                    await self.highrise.teleport(user.id, freeze_pos)
                return

            if user.id in self.flash_users and isinstance(destination, Position):
                await self.highrise.teleport(user.id, destination)
        except Exception as e:
            print(f"Error in on_user_move: {e}")

    async def run_user_emote_loop(self, user_id, emote_id, duration):
        """Loop an emote for a specific user."""
        while self.is_running and user_id in self.user_loops and self.user_loops[user_id] == emote_id:
            try:
                await self.highrise.send_emote(emote_id, user_id)
                await asyncio.sleep(duration if duration > 0 else 5)
            except Exception as e:
                if "User not in room" in str(e):
                    if user_id in self.user_loops:
                        del self.user_loops[user_id]
                else:
                    print(f"Error in user emote loop for {user_id}: {e}")
                break

    async def run_advertisement_loop(self):
        """Send a promotional message every 5 minutes."""
        # Initial wait before starting the loop
        await asyncio.sleep(60) 
        while self.is_running:
            try:
                if self.is_running:
                    await self.highrise.chat("This bot is created by @_inferno__, contact him if you want bot like this.")
                # Wait for 5 minutes (300 seconds) in small chunks to respond to shutdown
                for _ in range(300):
                    if not self.is_running:
                        break
                    await asyncio.sleep(1)
            except Exception as e:
                if not self.is_running:
                    break
                print(f"Error in advertisement loop: {e}")
                await asyncio.sleep(30) # Retry after 30 seconds if it fails



    async def on_chat(self, user: User, message: str) -> None:
        """Called when a chat message is received."""
        try:
            print(f"Chat from {user.username}: {message}")
            msg_lower = message.lower().strip()
            is_staff = await self.is_mod_or_owner(user.id, user.username)
            
            # Moderation Commands
            if msg_lower.startswith(("-freeze", "-unfreeze", "-mute", "-unmute", "-ban", "-unban", "-kick", "-ban", "-freeze""-unfreeze", "-unmute", "-unban")):
                if not is_staff:
                    await self.highrise.send_whisper(user.id, f"Sorry @{user.username}, only Moderators and Owners can use moderation commands.")
                    return

                parts = message.split()
                cmd = parts[0].lower()
                
                if cmd in ["-freeze", "!freeze"]:
                    if len(parts) < 2:
                        await self.highrise.send_whisper(user.id, f"Usage: {cmd} @username")
                        return
                    target_name = parts[1].replace("@", "")
                    target_id = await self.get_id_from_name(target_name)
                    if target_id:
                        # Get target's current position to freeze them there
                        room_users = await self.highrise.get_room_users()
                        target_pos = next((p for u, p in room_users.content if u.id == target_id), None)
                        if isinstance(target_pos, Position):
                            self.frozen_users[target_id] = target_pos
                            await self.highrise.send_whisper(user.id, f"@{target_name} has been frozen.")
                        else:
                            await self.highrise.send_whisper(user.id, f"Could not find position for @{target_name}.")
                    else:
                        await self.highrise.send_whisper(user.id, f"User @{target_name} not found.")
                    return

                elif cmd in ["-unfreeze", "!unfreeze"]:
                    if len(parts) < 2:
                        await self.highrise.send_whisper(user.id, f"Usage: {cmd} @username")
                        return
                    target_name = parts[1].replace("@", "")
                    target_id = await self.get_id_from_name(target_name)
                    if target_id in self.frozen_users:
                        del self.frozen_users[target_id]
                        await self.highrise.send_whisper(user.id, f"@{target_name} has been unfrozen.")
                    else:
                        await self.highrise.send_whisper(user.id, f"@{target_name} is not frozen.")
                    return

                elif cmd == "-mute":
                    if len(parts) < 3:
                        await self.highrise.send_whisper(user.id, "Usage: -mute @username (minutes)")
                        return
                    target_name = parts[1].replace("@", "")
                    try:
                        minutes = int(parts[2])
                    except:
                        await self.highrise.send_whisper(user.id, "Please provide a valid number of minutes.")
                        return
                    
                    target_id = await self.get_id_from_name(target_name)
                    if target_id:
                        try:
                            # Use server-side moderation to mute the user
                            # This actually prevents their chat from appearing in the room
                            await self.highrise.moderate_room(target_id, "mute", minutes * 60)
                            await self.highrise.send_whisper(user.id, f"@{target_name} has been muted for {minutes} minutes.")
                        except Exception as e:
                            print(f"Error muting {target_name}: {e}")
                            await self.highrise.send_whisper(user.id, f"Failed to mute @{target_name}. Check bot permissions.")
                    else:
                        await self.highrise.send_whisper(user.id, f"User @{target_name} not found.")
                    return

                elif cmd in ["-unmute", "!unmute"]:
                    if len(parts) < 2:
                        await self.highrise.send_whisper(user.id, f"Usage: {cmd} @username")
                        return
                    
                    target_name = parts[1].replace("@", "").lower()
                    target_id = await self.get_id_from_name(target_name)
                    
                    if target_id:
                        try:
                            # Using 1 second mute trick to clear previous mute state
                            # This is often the most reliable way to 'unmute' in Highrise
                            await self.highrise.moderate_room(target_id, "mute", 1)
                            await self.highrise.send_whisper(user.id, f"🔊 @{target_name} has been unmuted!")
                        except Exception as e:
                            print(f"Unmute error for {target_name}: {e}")
                            # Fallback to 'unmute' action just in case it's supported
                            try:
                                await self.highrise.moderate_room(target_id, "unmute")
                                await self.highrise.send_whisper(user.id, f"🔊 @{target_name} has been unmuted (action)!")
                            except:
                                await self.highrise.send_whisper(user.id, f"Failed to unmute @{target_name}. Please check bot permissions.")
                    else:
                        await self.highrise.send_whisper(user.id, f"User @{target_name} not found in the room.")
                    return

                elif cmd in ["-ban", "!ban"]:
                    if len(parts) < 2:
                        await self.highrise.send_whisper(user.id, f"Usage: {cmd} @username [minutes]")
                        return
                    target_name = parts[1].replace("@", "")
                    minutes = 0
                    if len(parts) > 2 and parts[2].isdigit():
                        minutes = int(parts[2])
                    
                    target_id = await self.get_id_from_name(target_name)
                    if target_id:
                        try:
                            # minutes=0 in SDK usually means permanent in room context, 
                            # but the request says "temporarily", so we use the minutes if provided.
                            # The SDK method for ban is 'ban_user'
                            await self.highrise.moderate_room(target_id, "ban", minutes * 60 if minutes > 0 else 3600)
                            self.banned_users[target_name.lower()] = target_id
                            await self.highrise.send_whisper(user.id, f"@{target_name} has been banned for {minutes if minutes > 0 else 60} minutes.")
                        except Exception as e:
                            await self.highrise.send_whisper(user.id, f"Failed to ban @{target_name}: {e}")
                    else:
                        await self.highrise.send_whisper(user.id, f"User @{target_name} not found.")
                    return

                elif cmd in ["-unban", "!unban"]:
                    if len(parts) < 2:
                        await self.highrise.send_whisper(user.id, "Usage: -unban @username")
                        return
                    
                    target_name = parts[1].replace("@", "").lower()
                    target_id = None
                    
                    # 1. Try finding in local banned list first
                    if target_name in self.banned_users:
                        target_id = self.banned_users[target_name]
                    else:
                        # 2. If not found, try searching globally (since user is not in room)
                        target_id = await self.get_user_id_webapi(target_name)
                    
                    if target_id:
                        try:
                            # Standard moderation unban
                            await self.highrise.moderate_room(target_id, "unban")
                            # SDK unban user (sometimes needed for global unban)
                            try:
                                await self.highrise.unban_user(target_id)
                            except: pass
                            
                            # Remove from local list if present
                            if target_name in self.banned_users:
                                del self.banned_users[target_name]
                                
                            await self.highrise.send_whisper(user.id, f"✅ @{target_name} has been unbanned!")
                        except Exception as e:
                            print(f"Unban error for {target_name}: {e}")
                            await self.highrise.send_whisper(user.id, f"Failed to unban @{target_name}: {e}")
                    else:
                        await self.highrise.send_whisper(user.id, f"Could not find @{target_name} to unban.")
                    return

                elif cmd == "-kick":
                    if len(parts) < 2:
                        await self.highrise.send_whisper(user.id, "Usage: -kick @username")
                        return
                    target_name = parts[1].replace("@", "")
                    target_id = await self.get_id_from_name(target_name)
                    if target_id:
                        try:
                            await self.highrise.moderate_room(target_id, "kick")
                            await self.highrise.send_whisper(user.id, f"@{target_name} has been kicked from the room.")
                        except Exception as e:
                            await self.highrise.send_whisper(user.id, f"Failed to kick @{target_name}: {e}")
                    else:
                        await self.highrise.send_whisper(user.id, f"User @{target_name} not found.")
                    return

            # Handle '-botfit @username' to copy outfit (Owner only)
            elif msg_lower.startswith("-botfit"):
                if self.is_owner(user.username):
                    # Ultra-Advanced Command with Multi-Phase Extraction
                    try:
                        # Extract target name (handles both '-botfit @name' and '-botfit name')
                        target_name = message[7:].strip().replace("@", "")
                        target_id = None

                        if not target_name:
                            # If no name is provided, copy the sender's outfit
                            target_name = user.username
                            target_id = user.id
                        
                        await self.highrise.send_whisper(user.id, f"🔍 Initializing deep scan for @{target_name}... ✨")


                        # --- PHASE 1: DISCOVERY & ID RESOLUTION ---
                        is_id = len(target_name) == 24 and all(c in "0123456789abcdef" for c in target_name.lower())
                        
                        # 1. Check room users first
                        if not target_id and not is_id:
                            try:
                                room_users_res = await self.highrise.get_room_users()
                                if not isinstance(room_users_res, Error):
                                    for u, _ in room_users_res.content:
                                        if u.username.lower() == target_name.lower():
                                            target_id = u.id
                                            target_name = u.username
                                            break
                            except: pass

                        # 2. Global Search if not in room
                        if not target_id and not is_id:
                            target_id = await self.get_user_id_webapi(target_name)

                        # --- PHASE 2: OUTFIT EXTRACTION ---
                        target_outfit = None
                        
                        # Strategy A: Gateway (SDK) - Best for live users/bots
                        if target_id or is_id:
                            try:
                                print(f"[DEBUG] Trying Gateway extraction for {target_id or target_name}")
                                outfit_res = await self.highrise.get_user_outfit(target_id or target_name)
                                if not isinstance(outfit_res, Error) and outfit_res.outfit:
                                    target_outfit = outfit_res.outfit
                            except Exception as e:
                                print(f"[DEBUG] Gateway extraction failed: {e}")

                        # Strategy B: WebAPI (Cloud) - Fallback for global/offline users
                        if not target_outfit:
                            try:
                                print(f"[DEBUG] Trying Cloud extraction for {target_name}")
                                target_outfit = await self.get_user_outfit_webapi(target_id or target_name)
                            except Exception as e:
                                print(f"[DEBUG] Cloud extraction failed: {e}")

                        if target_outfit is None:
                            await self.highrise.send_whisper(user.id, f"❌ Extraction failed for @{target_name}. Profile might be private or restricted.")
                            return
                        
                        if len(target_outfit) == 0:
                            await self.highrise.send_whisper(user.id, f"👻 @{target_name} is currently invisible or wearing nothing compatible!")
                            return

                        # 3. Visual Transformation & Execution
                        await self.highrise.send_whisper(user.id, f"👕 Style extracted! Applying @{target_name}'s look...")
                        
                        try:
                            # Apply the outfit
                            await self.highrise.set_outfit(target_outfit)
                            await self.highrise.send_whisper(user.id, f"🏁 ✨ 𝐏𝐄𝐑𝐅𝐄𝐂𝐓 𝐄𝐗𝐓𝐑𝐀𝐂𝐓𝐈𝐎𝐍! I'm now a 1:1 copy of @{target_name}! ✨")
                            
                            # Persistent Save
                            self.config["BOT_OUTFIT"] = [{"id": i.id, "amount": i.amount} for i in target_outfit]
                            self.save_config()
                        except Exception as e:
                            # Fallback: Clothing only
                            print(f"[DEBUG] Full outfit set failed: {e} | Trying Safe Mode Fallback...")
                            clothing_only = [i for i in target_outfit if "body" not in i.id.lower()]
                            try:
                                await self.highrise.set_outfit(clothing_only)
                                await self.highrise.send_whisper(user.id, f"✅ Look applied (Safe Mode)! Some body/face items were incompatible.")
                            except:
                                await self.highrise.send_whisper(user.id, f"❌ Failed to apply outfit: {str(e)[:50]}")
                    except Exception as e:
                        await self.highrise.send_whisper(user.id, f"❌ Error during extraction: {str(e)[:100]}")
                else:
                    await self.highrise.send_whisper(user.id, "Sorry, only owners can use -botfit.")
                return


            # Handle '-revertfit' to go back to original look (Owner only)
            elif msg_lower == "-revertfit":
                if not self.is_owner(user.username):
                    await self.highrise.send_whisper(user.id, "Only the owner can use -revertfit.")
                    return
                
                if self.original_outfit:
                    try:
                        await self.highrise.set_outfit(self.original_outfit)
                        await self.highrise.send_whisper(user.id, f"@{user.username}, I've reverted to my original outfit!")
                    except Exception as e:
                        print(f"Error in -revertfit: {e}")
                        await self.highrise.send_whisper(user.id, "Failed to revert outfit.")
                else:
                    await self.highrise.send_whisper(user.id, "I don't have my original outfit saved.")
                return

            # Handle '-setoriginal' to save current look as the base (Owner only)
            if msg_lower == "-setoriginal":
                if not self.is_owner(user.username):
                    await self.highrise.send_whisper(user.id, "Only the owner can use -setoriginal.")
                    return
                
                try:
                    outfit_res = await self.highrise.get_user_outfit(self.my_id)
                    if not isinstance(outfit_res, Error):
                        self.original_outfit = outfit_res.outfit
                        self.config["ORIGINAL_OUTFIT"] = [{"id": i.id, "amount": i.amount} for i in self.original_outfit]
                        self.save_config()
                        await self.highrise.send_whisper(user.id, "Current outfit saved as the bot's original look! ✅")
                    else:
                        await self.highrise.send_whisper(user.id, "Failed to fetch current outfit.")
                except Exception as e:
                    await self.highrise.send_whisper(user.id, f"Error saving outfit: {e}")
                return

            # Handle user emote loops
            
            if msg_lower == "-stopall":
                if await self.is_mod_or_owner(user.id, user.username):
                    if not self.user_loops:
                        await self.highrise.send_whisper(user.id, "No active user emote loops to stop.")
                        return
                    count = len(self.user_loops)
                    self.user_loops.clear()
                    await self.highrise.send_whisper(user.id, f"Stopped all {count} active user emote loops by @{user.username}.")
                else:
                    await self.highrise.send_whisper(user.id, f"Sorry @{user.username}, only owners and moderators can use -stopall.")
                return

            if msg_lower.startswith("-stop "):
                if await self.is_mod_or_owner(user.id, user.username):
                    target_username = message.split(" @")[-1].strip() if " @" in message else message.split(" ")[-1].strip()
                    target_username = target_username.replace("@", "")
                    
                    target_id = await self.get_id_from_name(target_username)
                    if target_id and target_id in self.user_loops:
                        del self.user_loops[target_id]
                        await self.highrise.send_whisper(user.id, f"Stopped @{target_username}'s emote loop by @{user.username}.")
                    else:
                        await self.highrise.send_whisper(user.id, f"User @{target_username} is not in an active emote loop.")
                else:
                    await self.highrise.send_whisper(user.id, f"Sorry @{user.username}, only owners and moderators can stop others' loops.")
                return

            if msg_lower in ["-stop", "stop"]:
                # Stop personal loop
                if user.id in self.user_loops:
                    del self.user_loops[user.id]
                    await self.highrise.send_whisper(user.id, f"@{user.username}, your emote loop has been stopped.")
                    return
                return

            # Handle '-(emote)all' to send emote to everyone (Owner/Mod)
            if msg_lower.startswith("-") and msg_lower.endswith("all"):
                emote_key = msg_lower[1:-3].strip()
                if emote_key in self.all_emotes:
                    if not await self.is_mod_or_owner(user.id, user.username):
                        await self.highrise.send_whisper(user.id, f"Sorry @{user.username}, only owners and moderators can use this.")
                        return
                    
                    emote_id = self.all_emotes[emote_key]["id"]
                    try:
                        room_users = await self.highrise.get_room_users()
                        if not isinstance(room_users, Error):
                            for target_user, pos in room_users.content:
                                if target_user.id != self.my_id:
                                    await self.highrise.send_emote(emote_id, target_user.id)
                            await self.highrise.send_whisper(user.id, f"Sent emote '{emote_key}' to everyone in the room!")
                    except Exception as e:
                        print(f"Error in -(emote)all: {e}")
                    return

            # Handle '(emote) @username' to loop for another user (Everyone)
            if " @" in msg_lower:
                parts = msg_lower.split(" @")
                emote_key = parts[0].strip()
                target_username = parts[1].strip()
                
                if emote_key in self.all_emotes:
                    target_id = await self.get_id_from_name(target_username)
                    if not target_id:
                        await self.highrise.send_whisper(user.id, f"User @{target_username} not found.")
                        return
                    
                    # Restriction: Regular users cannot force emotes on Owners/Moderators
                    target_is_staff = await self.is_mod_or_owner(target_id, target_username)
                    sender_is_staff = await self.is_mod_or_owner(user.id, user.username)
                    
                    if target_is_staff and not sender_is_staff:
                        await self.highrise.send_whisper(user.id, f"Sorry @{user.username}, you cannot force an emote loop on an Owner or Moderator.")
                        return
                    
                    emote_data = self.all_emotes[emote_key]
                    emote_id = emote_data["id"]
                    duration = emote_data.get("duration", 5)
                    
                    # Stop existing loop for target
                    self.user_loops[target_id] = emote_id
                    
                    # Find emote name and number
                    emote_name = emote_key
                    emote_no = "N/A"
                    for k, v in self.all_emotes.items():
                        if v["id"] == emote_id:
                            if k.isdigit(): emote_no = k
                            else: emote_name = k
                    
                    await self.highrise.send_whisper(user.id, f"@{user.username} started looping {emote_name} for @{target_username}! To stop say 'stop'")
                    asyncio.create_task(self.run_user_emote_loop(target_id, emote_id, duration))
                    return

            # Check if message is an emote name or number from the JSON (Personal Loop)
            if msg_lower in self.all_emotes:
                emote_data = self.all_emotes[msg_lower]
                emote_id = emote_data["id"]
                duration = emote_data.get("duration", 5)
                
                # Find the "other" key (name if number was typed, or vice versa)
                emote_name = msg_lower
                emote_no = "N/A"
                
                for k, v in self.all_emotes.items():
                    if v["id"] == emote_id:
                        if k.isdigit():
                            emote_no = k
                        else:
                            emote_name = k
                
                # Stop existing loop if any
                self.user_loops[user.id] = emote_id
                
                # Send confirmation message
                await self.highrise.send_whisper(user.id, f"@{user.username} is looping {emote_name} with emote no. {emote_no} \n To stop say 'stop'")
                
                # Start the loop task
                asyncio.create_task(self.run_user_emote_loop(user.id, emote_id, duration))
                return

            # Handle 'start' to control bot's own emote loop
            if message.lower() == "start":
                if not self.is_looping:
                    if not await self.is_mod_or_owner(user.id, user.username):
                        return
                    self.is_looping = True
                    await self.highrise.send_whisper(user.id, f"Bot's global emote loop started by @{user.username}!")
                return

            # Teleport user if they type a location name
            if message.lower() in self.tele_locations:
                loc_data = self.tele_locations[message.lower()]
                # Check VIP restriction - allow Mods/Owners
                if loc_data["vip"] and not (is_staff or self.is_vip(user.username)):
                    await self.highrise.send_whisper(user.id, f"Sorry @{user.username}, '{message.lower()}' is a VIP location.")
                    return
                
                p = loc_data["pos"]
                await self.highrise.send_whisper(user.id, f"✈️Teleport to {message.lower()}")
                await self.highrise.teleport(user.id, Position(p["x"], p["y"], p["z"], p["facing"]))
                return

            # Flash mode control (Everyone)
            elif message.lower() == "-flash on":
                self.flash_users.add(user.id)
                await self.highrise.send_whisper(user.id, f"Flash mode enabled for @{user.username}. Click anywhere to teleport!")
                return
            elif message.lower() == "-flash off":
                if user.id in self.flash_users:
                    self.flash_users.remove(user.id)
                await self.highrise.send_whisper(user.id, f"Flash mode disabled for @{user.username}.")
                return

            # Basic help command (always unlocked)
            if message.lower() == "-help":
                help_text = """💎✨ **PREMIUM BOT COMMANDS** ✨💎
🔥 *Powered by @_inferno__ 🔥

━━━━━━━━━━━━━━━━━━━━━━━

🛡️ **MODERATION CONTROL**
❖ `-freeze / -unfreeze @user` ➤ Control movement
❖ `-mute / -unmute @user [min]` ➤ Control chat access
❖ `-ban / -unban @user [min]` ➤ Room restriction
❖ `-kick @user` ➤ Instant removal
❖ `-stop @user` ➤ Stop user loop
❖ `-stopall` ➤ Stop all active loops

━━━━━━━━━━━━━━━━━━━━━━━

💃 **EMOTES & FUN ZONE**
❖ `-emotelist` ➤ View all emotes
❖ `-(emote) @user` ➤ Loop emote on user
❖ `-(emote)all` ➤ Emote for everyone
❖ `-stop` ➤ Stop your loop
❖ `-flash on/off` ➤ Click teleport mode
❖ `-punch @user` ➤ Fun interaction
❖ `-[reaction]all` ➤ React for all
❖ `-[reaction] @user [amount]` ➤ Custom reactions

━━━━━━━━━━━━━━━━━━━━━━━

🤖 **BOT & ROOM FEATURES**
❖ `-botfit [@user/bot]` ➤ Copy outfit
❖ `-setpose` ➤ Set bot position
❖ `-invite` ➤ Invite all users
❖ `-wallet` ➤ Check gold balance
❖ `-tip / -tipall [amount]` ➤ Send gold
❖ `-spam [msg] [amount]` ➤ Repeat message

━━━━━━━━━━━━━━━━━━━━━━━

🚀 **TELEPORTATION SYSTEM**
❖ `-tele [user/random] [loc/random]` ➤ Warp user
❖ `-void @user` ➤ Send outside map
❖ `-goto / -summon [user]` ➤ Teleport
❖ `-create tele / -createvip tele [loc]` ➤ Set warp
❖ `-listtele / -remtele [loc]` ➤ Manage warps

━━━━━━━━━━━━━━━━━━━━━━━

👥 **STAFF & ACCESS CONTROL**
❖ `-sub / -unsub [user]` ➤ Manage access
❖ `-owner / -remowner [user]` ➤ Owner control
❖ `-mod / -remmod [user]` ➤ Moderator control
❖ `-vip / -remvip [user]` ➤ VIP management
❖ `-rolelist` ➤ View all roles

━━━━━━━━━━━━━━━━━━━━━━━

🌟 **ELITE • FAST • POWERFUL** 🌟
💎 *Your Ultimate Premium Experience* 💎"""
                
                try:
                    # Send help menu via Direct Message
                    await self.highrise.send_message_bulk([user.id], help_text)
                    await self.highrise.send_whisper(user.id, f"@{user.username}, I've sent the categorized help menu to your DMs! 📩")
                except Exception as e:
                    print(f"Error sending help DM to {user.username}: {e}")
                    # Fallback to chat if DM fails
                    await self.highrise.send_whisper(user.id, f"@{user.username}, I couldn't DM you. Please check your privacy settings.")
                return

            elif message.lower() == "-emotelist":
                if not self.all_emotes:
                    await self.highrise.send_whisper(user.id, "No emotes found in the backup file.")
                    return
                
                # Format emotes: group numbers and names
                emote_items = []
                processed_ids = set()
                
                # Sort keys to maintain some order
                keys = sorted(self.all_emotes.keys(), key=lambda x: int(x) if x.isdigit() else 999999)
                
                for key in keys:
                    data = self.all_emotes[key]
                    e_id = data["id"]
                    if e_id not in processed_ids:
                        # Find the "name" for this ID
                        name = "Unknown"
                        number = "N/A"
                        for k, v in self.all_emotes.items():
                            if v["id"] == e_id:
                                if k.isdigit():
                                    number = k
                                else:
                                    name = k
                        emote_items.append(f"{number}. {name}")
                        processed_ids.add(e_id)

                # Chunking logic (max ~1000 chars per message)
                header = "Available Emotes (Type name or number to loop):\n"
                current_msg = header
                messages_to_send = []
                
                for item in emote_items:
                    if len(current_msg) + len(item) + 2 > 1000:
                        messages_to_send.append(current_msg)
                        current_msg = item + "\n"
                    else:
                        current_msg += item + "\n"
                messages_to_send.append(current_msg)

                try:
                    for msg in messages_to_send:
                        await self.highrise.send_message_bulk([user.id], msg)
                        await asyncio.sleep(0.5)
                    await self.highrise.send_whisper(user.id, f"@{user.username}, I've sent the emote list to your DMs!")
                except Exception as e:
                    print(f"Error sending emotelist DM to {user.username}: {e}")
                    await self.highrise.send_whisper(user.id, f"@{user.username}, I couldn't DM you the emote list.")
                return

            # Check if command
            if not message.startswith("-"):
                return

            # Check global lock (only owner can use commands if locked)
            if self.is_locked and not self.is_owner(user.username):
                # Don't even respond to non-owners if bot is locked
                return

            # Check subscription for all other commands
            # BUT: owners and mods should be allowed by default.
            if not is_staff and not self.is_subscribed(user.username) and not message.lower().startswith(("-sub", "-unsub", "-setpose")):
                await self.highrise.send_whisper(user.id, f"Sorry @{user.username}, you need to be subscribed to use this command. Ask the owner for access!")
                return

            # Set bot position (Owner only)
            elif message.lower() == "-setpose":
                if not self.is_owner(user.username):
                    await self.highrise.send_whisper(user.id, "Only the owner can use this command.")
                    return
                
                # Get the user's position
                room_users = await self.highrise.get_room_users()
                user_pos = None
                for room_user, pos in room_users.content:
                    if room_user.id == user.id:
                        user_pos = pos
                        break
                
                if user_pos:
                    # Save the position
                    self.config["SAVED_POSITION"] = {
                        "x": user_pos.x,
                        "y": user_pos.y,
                        "z": user_pos.z,
                        "facing": user_pos.facing
                    }
                    self.saved_pos = self.config["SAVED_POSITION"]
                    self.save_config()
                    
                    # Move the bot
                    await self.highrise.walk_to(user_pos)
                    await self.highrise.send_whisper(user.id, f"Position saved! I'll now stay here permanently.")
                    print(f"Bot position updated and saved by {user.username}: {user_pos}")
                else:
                    await self.highrise.send_whisper(user.id, "Could not find your position.")

            # Unsubscribe a user / Global Lock
            elif message.lower().startswith("-unsub"):
                parts = message.split()
                if len(parts) < 2:
                    # Self unsubscribe AND Global Lock
                    # Removed global lock logic

                    
                    if user.username.lower() in [s.lower() for s in self.subscribers]:
                        self.subscribers = [s for s in self.subscribers if s.lower() != user.username.lower()]
                        self.save_config()
                        await self.highrise.send_whisper(user.id, f"Hey @{user.username} ❌ You are now unsubscribed.If you want to join again anytime, just type -sub")
                    return

                # Target unsubscribe (Everyone can now use this)
                target_username = parts[1].replace("@", "")
                if target_username.lower() in [s.lower() for s in self.subscribers]:
                    self.subscribers = [s for s in self.subscribers if s.lower() != target_username.lower()]
                    self.save_config()
                    await self.highrise.send_whisper(user.id, f"Hey @{target_username} ❌ You are now unsubscribed.If you want to join again anytime, just type -sub")
                else:
                    await self.highrise.send_whisper(user.id, f"@{target_username} is not subscribed.")

            # Subscribe a user / Global Unlock
            elif message.lower().startswith("-sub"):
                # Everyone can now use -sub to unlock or subscribe users
                # Removed global unlock logic


                parts = message.split()
                if len(parts) < 2:
                    target_user = user
                else:
                    target_username = parts[1].replace("@", "")
                    # Try to find the user in the room
                    room_users = await self.highrise.get_room_users()
                    target_user = None
                    for room_user, pos in room_users.content:
                        if room_user.username.lower() == target_username.lower():
                            target_user = room_user
                            break
                    
                    if not target_user:
                        await self.highrise.send_whisper(user.id, f"User {target_username} not found in the room.")
                        return

                if target_user.username.lower() not in [s.lower() for s in self.subscribers]:
                    self.subscribers.append(target_user.username)
                    self.save_config()
                    


                    await self.highrise.send_whisper(user.id, f"Hey @{target_user.username} 👋 Welcome back! You are now subscribed ✅ Stay tuned for updates 🎶🔥")
                    
                    # Send DM to the user
                    try:
                        # Use send_message_bulk to send a direct message
                        # This works in v24.1.0+ and creates a conversation if needed
                        await self.highrise.send_message_bulk([target_user.id], f"Hello @{target_user.username}! You have been successfully subscribed to the Bot. All commands are now unlocked for you! Enjoy!")
                        print(f"DM sent to {target_user.username}")
                    except Exception as e:
                        print(f"Error sending DM to {target_user.username}: {e}")
                        # Fallback: whisper if DM fails
                        try:
                            await self.highrise.send_whisper(target_user.id, f"Hello @{target_user.username}! You have been successfully subscribed to the MusicBot. All commands are now unlocked for you! Enjoy!")
                        except:
                            pass
                else:
                    await self.highrise.send_whisper(user.id, f"@{target_user.username} is already subscribed.")

            # New Advanced Room Invite Handler
            elif msg_lower.startswith("-invite"):
                if await self.is_mod_or_owner(user.id, user.username):
                    parts = message.split()
                    
                    # Check for mentioned users
                    mentioned_users = [w[1:] for w in parts if w.startswith("@")]
                    
                    # Construct message (remove command and mentions)
                    msg_words = [w for w in parts[1:] if not w.startswith("@")]
                    invite_msg = " ".join(msg_words)
                    
                    if mentioned_users:
                        # Targeted Invite
                        await self.highrise.send_whisper(user.id, f"🔍 Resolving {len(mentioned_users)} users...")
                        target_ids = []
                        
                        # Resolve Usernames to IDs
                        for u_name in mentioned_users:
                            try:
                                # Try to find in room first (faster)
                                room_results = await self.highrise.get_room_users()
                                found = False
                                for ru, _ in room_results.content:
                                    if ru.username.lower() == u_name.lower():
                                        target_ids.append(ru.id)
                                        found = True
                                        break
                                
                                if not found:
                                    # Fallback to our ultra-robust WebAPI lookup
                                    uid = await self.get_user_id_webapi(u_name)
                                    if uid:
                                        target_ids.append(uid)
                                    else:
                                        print(f"User {u_name} not found.")
                            except Exception as e:
                                print(f"Error resolving {u_name}: {e}")
                        
                        if target_ids:
                            try:
                                # Send Text Message First (if provided)
                                if invite_msg:
                                    await self.highrise.send_message_bulk(target_ids, invite_msg)
                                    await asyncio.sleep(0.5)
                                
                                # Send Invite Card
                                # Signature: send_message_bulk(user_ids, content, message_type, room_id)
                                await self.highrise.send_message_bulk(target_ids, "Join our room!", "invite", self.room_id)
                                await self.highrise.send_whisper(user.id, f"✅ Created invites for {len(target_ids)} users!")
                            except Exception as e:
                                await self.highrise.send_whisper(user.id, f"❌ Error sending bulk invites: {e}")
                        else:
                            await self.highrise.send_whisper(user.id, "❌ No valid users found to invite.")
                        
                    else:
                        # Mass Invite (All Recent Conversations)
                        custom_msg = message[len("-invite"):].strip()
                        await self.highrise.send_whisper(user.id, "📨 Sending invites to all recent conversations...")
                        
                        try:
                            # Use SDK native get_conversations
                            conversations_resp = await self.highrise.get_conversations()
                            if isinstance(conversations_resp, Error):
                                await self.highrise.send_whisper(user.id, f"❌ Failed to fetch conversations: {conversations_resp.message}")
                                return
                                
                            conversations = conversations_resp.conversations
                            
                            inv_pool = [
                                "<#FFD700>Welcome to the VIP zone where the bass never stops. 🎧\n<#00FFFF>Let the rhythm take control and enjoy the elite vibes! ✨",
                                "<#FF4500>Turn up the volume and leave your worries at the door. 🎸\n<#FF69B4>This is where the best memories and loudest tracks live. 🌟",
                                "<#00FF00>Only premium beats and happy faces allowed in this space. 🎹\n<#FFD700>Grab a seat, stay a while, and feel the musical magic. 🌈",
                                "<#FF00FF>High energy and VIP treatment are our top priorities here. 🎤\n<#00FFFF>Let’s make this night legendary with the perfect playlist. 🔥",
                                "<#8A2BE2>Feel the pulse of the music deep inside your soul tonight. 🎷\n<#FF69B4>You’re in the best company with the ultimate VIP crew. 🥂",
                                "<#00FFFF>Good vibes only and the music is always playing loud. 🎻\n<#FFD700>Stay happy, stay hydrated, and keep the party going! 🌊",
                                "<#FFD700>Welcome to the inner circle where the melody meets luxury. 💎\n<#00FF00>Sit back and relax while the DJ spins your favorite hits. 💿",
                                "<#FF4500>Life is better when the beat drops and the room glows. 💡\n<#FF00FF>Enjoy your stay in the most exclusive hangout in town. 🏆",
                                "<#00FF00>Nothing but smiles and high-quality tunes in this room. 🎺\n<#8A2BE2>Let the harmony lift your spirits to a whole new level. 🚀",
                                "<#FF69B4>You’ve officially entered the VIP lounge of pure happiness. 🥂\n<#00FFFF>Every note is a celebration, so let’s dance the night away! 💃",
                                "<#FF4500>The playlist is fire and the company is even better. 🔥\n<#FFD700>Enjoy the VIP experience with every single heartbeat today. 💓",
                                "<#00FFFF>We play the music that makes your heart skip a beat. 🎶\n<#FF69B4>Welcome to your happy place where everyone is a star. ⭐",
                                "<#00FF00>Luxury is a feeling, and today it sounds like your song. 🎵\n<#FFD700>Stay VIP and let the good times roll endlessly for us. 🎡",
                                "<#FF00FF>Keep the energy high and the music even higher right now. 🔊\n<#00FFFF>This hangout is designed for those who love the elite life. 🎩",
                                "<#8A2BE2>Music is the language of the soul, and we speak it fluently. 🗣️\n<#FF69B4>Welcome to a room filled with joy and premium melodies. 🎼",
                                "<#00FFFF>Step into the spotlight and let the rhythm guide your way. 🔦\n<#FFD700>A VIP stay isn't complete without some world-class music. 🌍",
                                "<#FFD700>Your daily dose of happiness starts with this heavy bass. 🥁\n<#00FF00>Make yourself at home in our exclusive musical sanctuary. 🏰",
                                "<#FF4500>Every track is a masterpiece and every guest is a VIP. 🎨\n<#FF00FF>Let’s create a vibe that stays with us forever tonight. 🌌",
                                "<#00FF00>Relax, recharge, and revel in the sound of pure perfection. 🧘\n<#8A2BE2>This room is your ticket to a happy, musical escape. 🎫",
                                "<#FF69B4>Let the lyrics inspire you and the beat keep you moving. 💃\n<#00FFFF>Welcome to the most stylish hangout room on the map. 📍",
                                "<#FFD700>VIP access granted to the land of endless musical joy. 🗝️\n<#00FFFF>Turn the world off and turn the music all the way up. ⚡",
                                "<#FF4500>We don’t just play music; we create a VIP atmosphere. ☁️\n<#FF69B4>Stay happy and let the chords heal your spirit today. 🩹",
                                "<#00FF00>Bold beats for bold people in this exclusive hangout. 🦁\n<#FFD700>Enjoy the luxury of great sound and even better vibes. 🥂",
                                "<#FF00FF>Escape the ordinary and dive into a world of harmony. 🏊\n<#00FFFF>Your VIP stay is guaranteed to be full of musical surprises. 🎁",
                                "<#8A2BE2>Catch the wave of the melody and ride it to happiness. 🌊\n<#FF69B4>There’s no place like this room for a true music lover. 🎧",
                                "<#00FFFF>Shine bright like a diamond while the record keeps spinning. 💎\n<#FFD700>This is the VIP hangout where joy is the only rule. 📏",
                                "<#FFD700>Music sounds better when you're feeling like a total boss. 🕶️\n<#00FF00>Stay in the loop of happiness and high-end entertainment. ➰",
                                "<#FF4500>The ultimate soundtrack for your VIP lifestyle starts here. 🎹\n<#FF00FF>Let’s turn these moments into a symphony of great memories. 🎻",
                                "<#00FF00>Cheers to great tunes and even greater friends in this room. 🍻\n<#8A2BE2>May your stay be filled with rhythm and sparkling energy. ✨",
                                "<#FF69B4>A VIP experience means the music never gets boring. 🔄\n<#00FFFF>Keep smiling and keep vibing to the best tracks ever. 🍭",
                                "<#FF4500>Feel the magic in the air and the bass in the floor. 🪄\n<#FFD700>This is your VIP pass to a world of pure musical bliss. 🎟️",
                                "<#00FFFF>Happiness is a loud song and a room full of VIPs. 😊\n<#FF69B4>Enjoy every second of this top-tier hangout experience. 🥇",
                                "<#00FF00>Your presence is premium, and our music is top-shelf. 🍾\n<#FFD700>Let the melodies flow and the happy vibes grow stronger. 🌱",
                                "<#FF00FF>No stress allowed—only high-quality music and elite stays. 🚫\n<#00FFFF>Welcome to the VIP corner where life sounds beautiful. 🌈",
                                "<#8A2BE2>Tune in to the frequency of joy and stay for the rhythm. 📻\n<#FF69B4>We make sure every guest feels like the star of the show. 🌠",
                                "<#00FFFF>From jazz to pop, we have the VIP vibe you truly crave. 🎷\n<#FFD700>Stay happy and let the music be your best companion. 🤝",
                                "<#FFD700>The floor is yours and the playlist is absolutely legendary. 🕺\n<#00FF00>Make your VIP stay the highlight of your entire week. 🗓️",
                                "<#FF4500>Music is the heartbeat of this room, and you are the soul. ❤️\n<#FF00FF>Enjoy a happy, rhythmic hangout filled with luxury and loud beats. 🔊",
                                "<#00FF00>Surround yourself with elite sounds and positive energy. 🌀\n<#8A2BE2>This VIP room is your destination for musical perfection. 🏁",
                                "<#FF69B4>Let’s celebrate the good life with a melody that shines. 🥂\n<#00FFFF>You deserve a VIP stay that sounds as good as it looks. 📸",
                                "<#FF4500>Put your hands up for the VIP music experience of a lifetime. 🙌\n<#FFD700>Happiness is just a beat away in this exclusive hangout. 🎵",
                                "<#00FFFF>Experience the luxury of sound in our private VIP suite. 🛋️\n<#FF69B4>Keep the smile wide and the volume even wider today. 📢",
                                "<#00FF00>We take music seriously, but we take happiness even more. 😄\n<#FFD700>Welcome to a VIP stay that hits all the right notes. 🎼",
                                "<#FF00FF>Let the bass rumble and the good times crumble the walls. 🧱\n<#00FFFF>Stay VIP and enjoy the most rhythmic room in existence. 🎸",
                                "<#8A2BE2>Your happy place is now upgraded to VIP status officially. 🆙\n<#FF69B4>Relax into the music and let the vibes take the lead. 🧭",
                                "<#00FFFF>Golden tunes for our golden guests in this special room. 🟡\n<#FFD700>May your VIP stay be as bright as the loudest chorus. 🔆",
                                "<#FFD700>Music brings us together, but the VIP vibe keeps us here. 🔗\n<#00FF00>Enjoy a happy, rhythmic journey with every single track. 🛣️",
                                "<#FF4500>Elevate your mood with our handpicked VIP playlist today. 🎈\n<#FF00FF>This hangout is all about luxury, music, and pure fun. 🎢",
                                "<#00FF00>Dive into the deep end of the beat and feel the VIP chill. ❄️\n<#8A2BE2>Happiness is contagious when the music is this good. 🎤",
                                "<#FF69B4>The final track hasn't played yet, so keep the VIP party alive. 🕯️\n<#00FFFF>Stay happy, stay musical, and enjoy this elite hangout 🍹"
                            ]
                            count = 0
                            for conv in conversations:
                                try:
                                    current_msg = custom_msg if custom_msg else random.choice(inv_pool)
                                    await self.highrise.send_message(conv.id, current_msg)
                                    
                                    # Signature: send_message(conversation_id, content, type, room_id)
                                    await self.highrise.send_message(conv.id, "Join our room!", "invite", self.room_id)
                                    count += 1
                                    await asyncio.sleep(1.2) # Throttled
                                except Exception as e:
                                    print(f"Failed to invite conv {conv.id}: {e}")
                                    
                            await self.highrise.send_whisper(user.id, f"✅ Sent invites to {count} users!")
                            
                        except Exception as e:
                            print(f"Invite loop error: {e}")
                            await self.highrise.send_whisper(user.id, f"❌ Error sending mass invites: {e}")
                else:
                    await self.highrise.send_whisper(user.id, "ℹ️ You don't have permission to use this command.")
                return


            elif message.lower() == "-sublist":
                if not await self.is_mod_or_owner(user.id, user.username):
                    await self.highrise.send_whisper(user.id, "Only staff can see the subscriber list.")
                    return
                if not self.subscribers:
                    await self.highrise.send_whisper(user.id, "Subscriber list is empty.")
                else:
                    await self.highrise.send_whisper(user.id, f"Current Subscribers ({len(self.subscribers)}): {', '.join(self.subscribers)}")
                return

            # Role management commands
            elif message.lower().startswith("-owner"):
                if not self.is_owner(user.username):
                    await self.highrise.send_whisper(user.id, "Only an owner can add another owner.")
                    return
                parts = message.split()
                if len(parts) < 2:
                    await self.highrise.send_whisper(user.id, "Usage: -owner @username")
                    return
                target_username = parts[1].replace("@", "")
                if target_username.lower() not in [o.lower() for o in self.owners]:
                    self.owners.append(target_username)
                    self.save_config()
                    await self.highrise.send_whisper(user.id, f"@{target_username} is now an owner.")
                else:
                    await self.highrise.send_whisper(user.id, f"@{target_username} is already an owner.")

            elif message.lower().startswith("-remowner"):
                if not self.is_owner(user.username):
                    await self.highrise.send_whisper(user.id, "Only an owner can remove an owner.")
                    return
                parts = message.split()
                if len(parts) < 2:
                    await self.highrise.send_whisper(user.id, "Usage: -remowner @username")
                    return
                target_username = parts[1].replace("@", "")
                if target_username.lower() in [o.lower() for o in self.owners]:
                    if len(self.owners) <= 1:
                        await self.highrise.send_whisper(user.id, "Cannot remove the last owner.")
                        return
                    self.owners = [o for o in self.owners if o.lower() != target_username.lower()]
                    self.save_config()
                    await self.highrise.send_whisper(user.id, f"@{target_username} is no longer an owner.")
                else:
                    await self.highrise.send_whisper(user.id, f"@{target_username} is not an owner.")

            elif message.lower().startswith("-mod"):
                if not self.is_owner(user.username):
                    await self.highrise.send_whisper(user.id, "Only an owner can add a moderator.")
                    return
                parts = message.split()
                if len(parts) < 2:
                    await self.highrise.send_whisper(user.id, "Usage: -mod @username")
                    return
                
                target_username = parts[1].replace("@", "")
                if target_username.lower() not in [m.lower() for m in self.mods]:
                    self.mods.append(target_username)
                    self.save_config()
                    await self.highrise.send_whisper(user.id, f"@{target_username} is now a bot moderator.")
                else:
                    await self.highrise.send_whisper(user.id, f"@{target_username} is already a bot moderator.")

            elif message.lower().startswith("-remmod"):
                if not self.is_owner(user.username):
                    await self.highrise.send_whisper(user.id, "Only an owner can remove a moderator.")
                    return
                parts = message.split()
                if len(parts) < 2:
                    await self.highrise.send_whisper(user.id, "Usage: -remmod @username")
                    return
                
                target_username = parts[1].replace("@", "")
                if target_username.lower() in [m.lower() for m in self.mods]:
                    self.mods = [m for m in self.mods if m.lower() != target_username.lower()]
                    self.save_config()
                    await self.highrise.send_whisper(user.id, f"@{target_username} is no longer a bot moderator.")
                else:
                    await self.highrise.send_whisper(user.id, f"@{target_username} is not a bot moderator.")

            elif message.lower().startswith("-vip"):
                if not await self.is_mod_or_owner(user.id, user.username):
                    await self.highrise.send_whisper(user.id, "Only owner and moderators can add VIPs.")
                    return
                parts = message.split()
                if len(parts) < 2:
                    await self.highrise.send_whisper(user.id, "Usage: -vip @username")
                    return
                target_username = parts[1].replace("@", "")
                if target_username.lower() not in [v.lower() for v in self.vips]:
                    self.vips.append(target_username)
                    self.save_config()
                    await self.highrise.send_whisper(user.id, f"@{target_username} is now a VIP.")
                else:
                    await self.highrise.send_whisper(user.id, f"@{target_username} is already a VIP.")

            elif message.lower().startswith("-remvip"):
                if not await self.is_mod_or_owner(user.id, user.username):
                    await self.highrise.send_whisper(user.id, "Only owner and moderators can remove VIPs.")
                    return
                parts = message.split()
                if len(parts) < 2:
                    await self.highrise.send_whisper(user.id, "Usage: -remvip @username")
                    return
                target_username = parts[1].replace("@", "")
                if target_username.lower() in [v.lower() for v in self.vips]:
                    self.vips = [v for v in self.vips if v.lower() != target_username.lower()]
                    self.save_config()
                    await self.highrise.send_whisper(user.id, f"@{target_username} is no longer a VIP.")
                else:
                    await self.highrise.send_whisper(user.id, f"@{target_username} is not a VIP.")

            # Teleportation and Location Management
            elif message.lower().startswith("-goto"):
                if not await self.is_mod_or_owner(user.id, user.username):
                    await self.highrise.send_whisper(user.id, "Only owner and moderators can use -goto.")
                    return
                parts = message.split()
                if len(parts) < 2:
                    await self.highrise.send_whisper(user.id, "Usage: -goto @username")
                    return
                target_username = parts[1].replace("@", "")
                room_users = await self.highrise.get_room_users()
                target_user_pos = next(((u, p) for u, p in room_users.content if u.username.lower() == target_username.lower()), None)
                if target_user_pos and isinstance(target_user_pos[1], Position):
                    await self.highrise.teleport(user.id, target_user_pos[1])
                else:
                    await self.highrise.send_whisper(user.id, f"Could not find @{target_username} or their position.")

            elif message.lower().startswith("-summon"):
                if not await self.is_mod_or_owner(user.id, user.username):
                    await self.highrise.send_whisper(user.id, "Only owner and moderators can use -summon.")
                    return
                parts = message.split()
                if len(parts) < 2:
                    await self.highrise.send_whisper(user.id, "Usage: -summon @username")
                    return
                target_username = parts[1].replace("@", "")
                room_users = await self.highrise.get_room_users()
                # Find current user's position to summon to
                summoner_pos = next((p for u, p in room_users.content if u.id == user.id), None)
                target_user = next((u for u, p in room_users.content if u.username.lower() == target_username.lower()), None)
                
                if target_user and isinstance(summoner_pos, Position):
                    await self.highrise.teleport(target_user.id, summoner_pos)
                    await self.highrise.send_whisper(user.id, f"Summoned @{target_username} to you.")
                else:
                    await self.highrise.send_whisper(user.id, f"Could not find @{target_username} or your position.")

            elif message.lower().startswith("-create tele"):
                if not self.is_owner(user.username):
                    await self.highrise.send_whisper(user.id, "Only an owner can create teleport locations.")
                    return
                parts = message.split()
                if len(parts) < 3:
                    await self.highrise.send_whisper(user.id, "Usage: -create tele (location name)")
                    return
                loc_name = " ".join(parts[2:]).lower()
                room_users = await self.highrise.get_room_users()
                user_pos = next((p for u, p in room_users.content if u.id == user.id), None)
                
                if isinstance(user_pos, Position):
                    self.tele_locations[loc_name] = {
                        "pos": {"x": user_pos.x, "y": user_pos.y, "z": user_pos.z, "facing": user_pos.facing},
                        "vip": False
                    }
                    self.save_config()
                    await self.highrise.teleport(user.id, user_pos)
                    await self.highrise.send_whisper(user.id, f"Location '{loc_name}' created at your position!")
                else:
                    await self.highrise.send_whisper(user.id, "Could not find your position.")

            elif message.lower().startswith("-createvip tele"):
                if not self.is_owner(user.username):
                    await self.highrise.send_whisper(user.id, "Only an owner can create VIP locations.")
                    return
                parts = message.split()
                if len(parts) < 3:
                    await self.highrise.send_whisper(user.id, "Usage: -createvip tele (location name)")
                    return
                loc_name = " ".join(parts[2:]).lower()
                room_users = await self.highrise.get_room_users()
                user_pos = next((p for u, p in room_users.content if u.id == user.id), None)
                
                if isinstance(user_pos, Position):
                    self.tele_locations[loc_name] = {
                        "pos": {"x": user_pos.x, "y": user_pos.y, "z": user_pos.z, "facing": user_pos.facing},
                        "vip": True
                    }
                    self.save_config()
                    await self.highrise.teleport(user.id, user_pos)
                    await self.highrise.send_whisper(user.id, f"VIP Location '{loc_name}' created at your position!")
                else:
                    await self.highrise.send_whisper(user.id, "Could not find your position.")

            elif message.lower().startswith("-tele"):
                parts = message.split()
                if len(parts) < 3:
                    await self.highrise.send_whisper(user.id, "Usage: -tele @username (location name)")
                    return
                target_username = parts[1].replace("@", "")
                loc_name = " ".join(parts[2:]).lower()
                
                # Support random location
                if loc_name == "random":
                    if not self.tele_locations:
                        await self.highrise.send_whisper(user.id, "No locations saved yet.")
                        return
                    loc_name = random.choice(list(self.tele_locations.keys()))
                
                if loc_name not in self.tele_locations:
                    await self.highrise.send_whisper(user.id, f"Location '{loc_name}' does not exist.")
                    return
                
                loc_data = self.tele_locations[loc_name]
                
                # Check VIP restriction - bypass for staff
                if not is_staff and loc_data["vip"] and not (self.is_owner(target_username) or self.is_vip(target_username)):
                    await self.highrise.send_whisper(user.id, f"Only VIPs can teleport to '{loc_name}'.")
                    return
                
                room_users = await self.highrise.get_room_users()
                if isinstance(room_users, Error):
                    await self.highrise.send_whisper(user.id, f"Error fetching room users: {room_users.message}")
                    return

                # Support random user
                if target_username.lower() == "random":
                    # Filter out the bot itself
                    eligible_users = [u for u, p in room_users.content if u.id != self.my_id]
                    if not eligible_users:
                        await self.highrise.send_whisper(user.id, "No users in the room to teleport.")
                        return
                    target_user = random.choice(eligible_users)
                    target_username = target_user.username
                else:
                    target_user = next((u for u, p in room_users.content if u.username.lower() == target_username.lower()), None)
                
                if target_user:
                    p = loc_data["pos"]
                    await self.highrise.send_whisper(user.id, f"✈️Teleport @{target_username} to {loc_name}")
                    await self.highrise.teleport(target_user.id, Position(p["x"], p["y"], p["z"], p["facing"]))
                else:
                    await self.highrise.send_whisper(user.id, f"User @{target_username} not found in room.")

            elif message.lower() == "-listtele":
                if not await self.is_mod_or_owner(user.id, user.username):
                    await self.highrise.send_whisper(user.id, "Only owner and moderators can see the telelist.")
                    return
                if not self.tele_locations:
                    await self.highrise.send_whisper(user.id, "No teleport locations created yet.")
                    return
                locs = []
                for name, data in self.tele_locations.items():
                    locs.append(f"{name}{' (VIP)' if data['vip'] else ''}")
                await self.highrise.send_whisper(user.id, f"Available locations: {', '.join(locs)}")

            elif message.lower().startswith("-remtele"):
                if not self.is_owner(user.username):
                    await self.highrise.send_whisper(user.id, "Only an owner can remove teleport locations.")
                    return
                parts = message.split()
                if len(parts) < 2:
                    await self.highrise.send_whisper(user.id, "Usage: -remtele (location name)")
                    return
                loc_name = " ".join(parts[1:]).lower()
                if loc_name in self.tele_locations:
                    del self.tele_locations[loc_name]
                    self.save_config()
                    await self.highrise.send_whisper(user.id, f"Location '{loc_name}' removed.")
                else:
                    await self.highrise.send_whisper(user.id, f"Location '{loc_name}' not found.")

            elif message.lower().startswith("-void"):
                if not is_staff:
                    await self.highrise.send_whisper(user.id, "Only owner and moderators can use -void.")
                    return
                parts = message.split()
                if len(parts) < 2:
                    await self.highrise.send_whisper(user.id, "Usage: -void @username")
                    return
                target_username = parts[1].replace("@", "")
                
                room_users = await self.highrise.get_room_users()
                if isinstance(room_users, Error):
                    await self.highrise.send_whisper(user.id, f"Error fetching room users: {room_users.message}")
                    return
                
                target_user = next((u for u, p in room_users.content if u.username.lower() == target_username.lower()), None)
                
                if target_user:
                    # Coordinate far outside the map
                    void_pos = Position(999, 999, 999, "FrontRight")
                    await self.highrise.send_whisper(user.id, f"🌌 Sending @{target_username} to the VOID!")
                    await self.highrise.teleport(target_user.id, void_pos)
                else:
                    await self.highrise.send_whisper(user.id, f"User @{target_username} not found in room.")

            elif message.lower() == "-wallet":
                if not await self.is_mod_or_owner(user.id, user.username):
                    await self.highrise.send_whisper(user.id, "Only owner and moderators can check the wallet.")
                    return
                
                try:
                    wallet = await self.highrise.get_wallet()
                    if isinstance(wallet, Error):
                        await self.highrise.send_whisper(user.id, f"Error fetching wallet: {wallet.message}")
                        return
                    
                    # Find gold balance only
                    gold_amount = 0
                    for item in wallet.content:
                        if item.type == "gold":
                            gold_amount = item.amount
                            break
                    
                    await self.highrise.send_whisper(user.id, f"Bot Gold Balance: {gold_amount} gold")
                except Exception as e:
                    print(f"Error in -wallet: {e}")
                    await self.highrise.send_whisper(user.id, "An error occurred while fetching the wallet.")

            elif message.lower().startswith("-tipall"):
                if not await self.is_mod_or_owner(user.id, user.username):
                    await self.highrise.send_whisper(user.id, "Only owner and admins (moderators) can use -tipall.")
                    return
                
                # Check current gold balance
                bot_gold = await self.get_bot_gold()
                if bot_gold <= 1:
                    await self.highrise.send_whisper(user.id, "bot gold wallet is empty")
                    return

                parts = message.split()
                if len(parts) < 2:
                    await self.highrise.send_whisper(user.id, "Usage: -tipall (amount)")
                    return
                
                amount_str = parts[1]
                bar_id = self.get_gold_bar_id(amount_str)
                if not bar_id:
                    await self.highrise.send_whisper(user.id, f"Invalid amount. Allowed: 1, 5, 10, 50, 100, 500, 1000, 5000, 10000")
                    return
                
                try:
                    room_users = await self.highrise.get_room_users()
                    if isinstance(room_users, Error):
                        await self.highrise.send_whisper(user.id, f"Error getting room users: {room_users.message}")
                        return
                    
                    count = 0
                    for target_user, pos in room_users.content:
                        if target_user.id == self.my_id:
                            continue
                        res = await self.highrise.tip_user(target_user.id, bar_id)
                        if res == "success":
                            count += 1
                        elif res == "insufficient_funds":
                            await self.highrise.send_whisper(user.id, f"Bot ran out of gold after tipping {count} users!")
                            return
                    
                    await self.highrise.send_whisper(user.id, f"Successfully tipped {count} users in the room!")
                except Exception as e:
                    print(f"Error in -tipall: {e}")
                    await self.highrise.send_whisper(user.id, "An error occurred during bulk tipping.")

            elif message.lower().startswith("-tip"):
                if not await self.is_mod_or_owner(user.id, user.username):
                    await self.highrise.send_whisper(user.id, "Only owner and admins (moderators) can use -tip.")
                    return
                
                # Check current gold balance
                bot_gold = await self.get_bot_gold()
                if bot_gold <= 1:
                    await self.highrise.send_whisper(user.id, "bot gold wallet is empty")
                    return

                parts = message.split()
                if len(parts) < 3:
                    await self.highrise.send_whisper(user.id, "Usage: -tip @username (amount)")
                    return
                
                target_username = parts[1].replace("@", "")
                amount_str = parts[2]
                bar_id = self.get_gold_bar_id(amount_str)
                if not bar_id:
                    await self.highrise.send_whisper(user.id, f"Invalid amount. Allowed: 1, 5, 10, 50, 100, 500, 1000, 5000, 10000")
                    return
                
                try:
                    room_users = await self.highrise.get_room_users()
                    target_user = next((u for u, p in room_users.content if u.username.lower() == target_username.lower()), None)
                    if not target_user:
                        await self.highrise.send_whisper(user.id, f"User {target_username} not found in room.")
                        return
                    
                    res = await self.highrise.tip_user(target_user.id, bar_id)
                    if res == "success":
                        await self.highrise.send_whisper(user.id, f"Successfully tipped @{target_username} {amount_str} gold!")
                    elif res == "insufficient_funds":
                        await self.highrise.send_whisper(user.id, "Bot has insufficient funds for this tip.")
                    else:
                        await self.highrise.send_whisper(user.id, f"Tipping failed: {res}")
                except Exception as e:
                    print(f"Error in -tip: {e}")
                    await self.highrise.send_whisper(user.id, "An error occurred while tipping.")

            elif message.lower().startswith("-punch"):
                parts = message.split()
                if len(parts) < 2:
                    await self.highrise.send_whisper(user.id, "Usage: -punch @username")
                    return
                
                target = parts[1].replace("@", "")
                uid = await self.get_id_from_name(target)
                if uid:
                    # User who typed command punches
                    await self.highrise.send_emote("emoji-punch", user.id)
                    await asyncio.sleep(0.5)
                    # Target user dies
                    await self.highrise.send_emote("emote-death2", uid)
                else:
                    await self.highrise.send_whisper(user.id, f"User @{target} not found in the room.")

            # Reaction commands
            elif any(message.lower().startswith(f"-{reaction}") for reaction in ["heart", "wink", "clap", "thumbs"]):
                if not await self.is_mod_or_owner(user.id, user.username):
                    await self.highrise.send_whisper(user.id, "Only owner and moderators can use reaction commands.")
                    return

                parts = message.lower().split()
                command = parts[0][1:] # e.g., "heartall" or "clap"
                
                reaction_map = {"heart": "heart", "wink": "wink", "clap": "clap", "thumbs": "thumbs"}
                reaction_name = command.replace("all", "")
                reaction_id = reaction_map.get(reaction_name)

                if not reaction_id:
                    return # Should not happen with the startswith check

                # Bulk reaction to all users
                if command.endswith("all"):
                    try:
                        room_users = await self.highrise.get_room_users()
                        if isinstance(room_users, Error):
                            await self.highrise.send_whisper(user.id, f"Error getting room users: {room_users.message}")
                            return
                        
                        for target_user, pos in room_users.content:
                            if target_user.id != self.my_id:
                                await self.highrise.react(reaction_id, target_user.id)
                        await self.highrise.send_whisper(user.id, f"Sent a {reaction_name} to everyone!")
                    except Exception as e:
                        print(f"Error in -{command}: {e}")
                    return

                # Reaction to a specific user
                if len(parts) < 2:
                    await self.highrise.send_whisper(user.id, f"Usage: -{reaction_name} @username [amount]")
                    return
                
                target_username = parts[1].replace("@", "")
                amount = 1
                if len(parts) > 2 and parts[2].isdigit():
                    amount = int(parts[2])
                
                target_user_id = await self.get_id_from_name(target_username)
                if not target_user_id:
                    await self.highrise.send_whisper(user.id, f"User @{target_username} not found.")
                    return
                
                try:
                    for _ in range(amount):
                        await self.highrise.react(reaction_id, target_user_id)
                        await asyncio.sleep(0.3) # Reduced delay
                    await self.highrise.send_whisper(user.id, f"Sent {amount} {reaction_name}(s) to @{target_username}!")
                except Exception as e:
                    print(f"Error in -{reaction_name}: {e}")

            elif message.lower().startswith("-botroom "):
                if self.is_owner(user.username):
                    parts = message.split()
                    if len(parts) < 2:
                        await self.highrise.send_whisper(user.id, "💡 Usage: -botroom [room_link/id]")
                        return
                    
                    room_input = parts[1]
                    new_room_id = room_input
                    
                    # 1. Parse Room ID from various link formats
                    if "highrise.game/room/" in room_input:
                        new_room_id = room_input.split("highrise.game/room/")[-1].split("?")[0].split("&")[0]
                    elif "high.rs/room?id=" in room_input:
                        new_room_id = room_input.split("high.rs/room?id=")[-1].split("&")[0]
                    
                    # 2. Inform the user
                    await self.highrise.send_whisper(user.id, f"🚀 <#00FF00>Switching to new room! ID: {new_room_id}\n🌀 The bot will join there in a few seconds... (Bypassing cooldown)")
                    await asyncio.sleep(0.5)
                    
                    # 3. Update Configuration Files
                    try:
                        token_clean = self.config.get("API_TOKEN", "").strip()
                        # Persist data across rooms:
                        try:
                            if not os.path.exists("settings"):
                                os.makedirs("settings")

                            # Ensure current settings are flushed to disk first
                            self.save_config()

                            new_settings_file = os.path.join("settings", f"settings_{new_room_id}.json")
                            existing = {}
                            if os.path.exists(new_settings_file):
                                try:
                                    with open(new_settings_file, "r") as f:
                                        existing = json.load(f) or {}
                                except:
                                    existing = {}

                            merged = dict(existing)
                            merged.update(self.config)

                            merged["owners"] = self.owners
                            merged["mods"] = self.mods
                            merged["vips"] = self.vips

                            tmp_file = new_settings_file + ".tmp"
                            with open(tmp_file, "w") as f:
                                json.dump(merged, f, indent=4)
                            try:
                                os.replace(tmp_file, new_settings_file)
                            except OSError:
                                if os.path.exists(new_settings_file):
                                    os.remove(new_settings_file)
                                os.rename(tmp_file, new_settings_file)
                        except Exception as e:
                            print(f"[WARN] Failed to migrate settings to new room: {e}")
                        
                        if os.path.exists("bots_config.json"):
                            try:
                                with open("bots_config.json", "r") as f:
                                    bots_data = json.load(f)
                                
                                found = False
                                if isinstance(bots_data, list):
                                    for b in bots_data:
                                        if b.get("token", "").strip() == token_clean:
                                            b["room_id"] = new_room_id
                                            b["force_restart"] = True
                                            found = True
                                            break
                                    
                                    if found:
                                        with open("bots_config.json", "w") as f:
                                            json.dump(bots_data, f, indent=4)
                            except Exception as e:
                                print(f"Error updating bots_config: {e}")
                        
                        if os.path.exists("config.json"):
                            try:
                                # Update self.config before save_config
                                self.config["ROOM_ID"] = new_room_id
                                self.config["room_id"] = new_room_id
                                self.config["force_restart"] = True
                            except Exception as e:
                                print(f"Error updating config.json: {e}")
                                
                        # 4. Exit to trigger manager restart
                        self.save_config()
                        await asyncio.sleep(1)
                        os._exit(0)
                        
                    except Exception as e:
                        print(f"[ERROR] -botroom error: {e}")
                        await self.highrise.send_whisper(user.id, f"❌ <#FF0000>Failed to update room configuration: {e}")
                else: 
                    await self.highrise.send_whisper(user.id, "ℹ️ You don't have permission to use this command.")
                return

            elif message.lower() == "-rolelist":
                if not self.is_owner(user.username):
                    await self.highrise.send_whisper(user.id, "Only the owner can see the role list.")
                    return

                try:
                    # Construct individual role strings
                    owners_list = "\n".join([f"👑 @{o}" for o in self.owners]) if self.owners else "None"
                    mods_list = "\n".join([f"🔰 @{m}" for m in self.mods]) if self.mods else "None"
                    vips_list = "\n".join([f"💎 @{v}" for v in self.vips]) if self.vips else "None"

                    # Ultimate Premium Role List Message
                    response = (
                        "✨ **ROLE LIST** ✨\n\n"
                        "━━━━━━━━━━━━━━━\n\n"
                        "👑 **Room Owners**\n"
                        f"{owners_list}\n\n"
                        "🔰 **Bot Moderators**\n"
                        f"{mods_list}\n\n"
                        "💎 **VIP Members**\n"
                        f"{vips_list}\n\n"
                        "━━━━━━━━━━━━━━━\n\n"
                        "📜 **Show Roles**\n"
                        "`-rolelist` ➤ Displays in order:\n"
                        "👑 Owner → 🔰 Moderator → 💎 VIP\n\n"
                        "━━━━━━━━━━━━━━━\n"
                        "⚡ Keep your room clean & organized ⚡"
                    )

                    try:
                        # Send full list via DM to bypass whisper length limits
                        await self.highrise.send_message_bulk([user.id], response)
                        await self.highrise.send_whisper(user.id, f"@{user.username}, I've sent the full Role List to your DMs! 📩")
                    except:
                        # Fallback to a compact version in whisper if DM fails
                        compact_msg = f"✨ Bot Roles: Owners({len(self.owners)}), Mods({len(self.mods)}), VIPs({len(self.vips)}). Check DMs for names!"
                        await self.highrise.send_whisper(user.id, compact_msg)
                except Exception as e:
                    print(f"Error in -rolelist: {e}")
                    await self.highrise.send_whisper(user.id, "An error occurred while fetching the role list.")
                return

            elif message.lower().startswith("-spam"):
                if not await self.is_mod_or_owner(user.id, user.username):
                    await self.highrise.send_whisper(user.id, "Only owner and moderators can use -spam.")
                    return
                
                parts = message.split()
                if len(parts) < 3:
                    await self.highrise.send_whisper(user.id, "Usage: -spam (message) (amount)")
                    return
                
                try:
                    amount = int(parts[-1])
                    spam_message = " ".join(parts[1:-1])

                    if amount > 100: # Prevent abuse
                        await self.highrise.send_whisper(user.id, "Spam amount cannot exceed 100.")
                        return

                    for _ in range(amount):
                        await self.highrise.chat(spam_message)
                        await asyncio.sleep(0.5) # Delay to prevent flooding
                except ValueError:
                    await self.highrise.send_whisper(user.id, "Invalid amount. Please provide a number.")
                except Exception as e:
                    print(f"Error in -spam: {e}")

            # Example of a locked command (or any command starting with -)
            elif message.startswith("-"):
                if not self.is_subscribed(user.username):
                    await self.highrise.send_whisper(user.id, f"Sorry @{user.username}, you need to be subscribed to use this command. Ask the owner for access!")
                    return
                
                # If they ARE subscribed, handle other commands here
                # (None specified by the user yet, but they will be unlocked)
                pass

        except BaseException as e:
            print(f"ERROR in on_chat: {type(e).__name__}: {e}")
            traceback.print_exc()

    async def on_user_leave(self, user: User) -> None:
        """Called when a user leaves the room."""
        try:
            print(f"User {user.username} left.")
        except BaseException as e:
            print(f"ERROR in on_user_leave: {type(e).__name__}: {e}")
            traceback.print_exc()

    async def get_username_from_id(self, user_id: str) -> str | None:
        # Fast Path 1: Check reverse cache
        for name, uid in self.id_cache.items():
            if uid == user_id:
                return name
                
        # Fast Path 2: Check users currently inside the room
        try:
            room_users = await self.highrise.get_room_users()
            if not isinstance(room_users, Error):
                for u, _ in room_users.content:
                    if u.id == user_id:
                        self.id_cache[u.username.lower()] = u.id # update cache
                        return u.username
        except:
            pass
            
        # Slow Path: Web API fallback
        session = await self._get_session()
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Accept": "application/json"}
        url = f"https://webapi.highrise.game/users/{user_id}"
        try:
            async with session.get(url, headers=headers, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if isinstance(data, dict):
                        user_data = data.get("user")
                        if isinstance(user_data, dict):
                            username = user_data.get("username")
                            if username:
                                self.id_cache[username.lower()] = user_id
                                return username
        except Exception as e:
            print(f"Error fetching username from ID: {e}")
        return None

    async def on_message(self, user_id: str, conversation_id: str, is_new_conversation: bool) -> None:
        """Called when a message is received in a conversation/DM."""
        try:
            # Check the latest message
            response = await self.highrise.get_messages(conversation_id)
            if isinstance(response, Error) or not response.messages:
                return
            
            message = response.messages[0]
            if message.sender_id != self.my_id:
                msg_lower = message.content.lower().strip()
                if msg_lower == "-sub":
                    username = await self.get_username_from_id(user_id)
                    if not username:
                        await self.highrise.send_message(conversation_id, "❌ Sorry, I couldn't resolve your username for subscription. Try again later or use the room command.")
                        return
                    
                    if username.lower() not in [s.lower() for s in self.subscribers]:
                        self.subscribers.append(username)
                        self.save_config()
                        await self.highrise.send_message(conversation_id, f"Hey @{username} 👋 Welcome back! You are now subscribed ✅ Stay tuned for updates 🎶🔥")
                    else:
                        await self.highrise.send_message(conversation_id, f"@{username} is already subscribed.")
                        
                elif msg_lower == "-unsub":
                    username = await self.get_username_from_id(user_id)
                    if not username:
                        await self.highrise.send_message(conversation_id, "❌ Sorry, I couldn't resolve your username for unsubscription. Try again later or use the room command.")
                        return

                    if username.lower() in [s.lower() for s in self.subscribers]:
                        self.subscribers = [s for s in self.subscribers if s.lower() != username.lower()]
                        self.save_config()
                        await self.highrise.send_message(conversation_id, f"Hey @{username} ❌ You are now unsubscribed. If you want to join again anytime, just type -sub")
                    else:
                        await self.highrise.send_message(conversation_id, f"@{username} is not subscribed.")
        except Exception as e:
            print(f"Error in on_message: {e}")

def run_bot():
    """Helper to run the bot using config.json or environment variables."""
    import time
    while True:
        try:
            room_id = os.getenv("ROOM_ID")
            api_token = os.getenv("API_TOKEN")

            # Try loading from config.json if not in env
            if not room_id or not api_token:
                try:
                    with open("config.json", "r") as f:
                        config = json.load(f)
                        room_id = config.get("ROOM_ID")
                        api_token = config.get("API_TOKEN")
                        
                        # Reset force_restart if present
                        if config.get("force_restart"):
                            config["force_restart"] = False
                            with open("config.json", "w") as fw:
                                json.dump(config, fw, indent=4)
                except FileNotFoundError:
                    print("ERROR: config.json not found")
                except Exception as e:
                    print(f"ERROR loading config: {e}")

            if not room_id or "YOUR_ROOM_ID" in room_id:
                print("Error: ROOM_ID not found in .env or config.json. Exiting...")
                break
            if not api_token or "YOUR_API_TOKEN" in api_token:
                print("Error: API_TOKEN not found in .env or config.json. Exiting...")
                break

            # Use the highrise-bot CLI module to run
            print(f"\n🚀 Launching bot for room: {room_id} 🚀\n")
            exit_code = os.system(f"python -m highrise main:MusicBot {room_id} {api_token}")
            
            print(f"\nBot process ended (code {exit_code}). Restarting in 1 second...")
            time.sleep(1)
            
        except KeyboardInterrupt:
            print("\nShutting down bot manager...")
            break
        except BaseException as e:
            print(f"FATAL ERROR in run_bot: {type(e).__name__}: {e}")
            time.sleep(5)

if __name__ == "__main__":
    try:
        run_bot()
    except BaseException as e:
        print(f"CRITICAL ERROR: {type(e).__name__}: {e}")
        traceback.print_exc()
        import sys
        sys.exit(1)
