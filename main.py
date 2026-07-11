from difflib import SequenceMatcher
import random
import os
from dotenv import load_dotenv
from typing import Union
import discord
from discord.ext import commands

FilePath="./variables.env"
try:
    load_dotenv(FilePath)
    DISCORD_TOKEN = os.getenv("discordBotToken")
except Exception as e:
    print(f"Error loading environment variables loading  backup: {e}")


class Tracker():
    _instance = None
    _initialized = False
    
    def __new__():
        if Tracker._instance == None:
            Tracker._instance = super().__new__(Tracker)
        return Tracker._instance
    
    def __init__(self) -> None:
        if not self._initialized:
            self._users_sent_to = [] 
            self._users_not_found = []
            Tracker._initialized = True 
    def user_sent_to_add(self,data):
        if type(data) == str:
            self._users_sent_to.append(data)
            pass
    def user_sent_to_get(self):
        if len(self._users_sent_to) > 1:
            return self._users_sent_to
        else:
            return 0
USERS_MAP={}
users_sent_to=[]
users_not_found=[]

DM_MESSAGE_TEMPLATE = "Hohoho, you are now a secret santa! Your receipients name is: {receiver_name}. Merry Christmas!"

PREFIX = "s!"
#Finds the closest matching name in the list (used for removal).
    
def match_close_name(rem_name, current_names):
    best_match = None
    baseline = 0.0
    for name in current_names:
        if rem_name.upper() == name.upper(): #makes the match case esier to find 
            return name 
    for name in current_names:
        ratio = SequenceMatcher(None, rem_name.upper(), name.upper()).ratio() #if the name wasnt an exact match, check if it was close enough to be considered a match (0.5 or higher)
        if ratio > baseline:
            best_match = name
            baseline = ratio
    if baseline >= 0.5:
        return best_match
    else:
        return None


class SantaCommands(commands.Cog):#define the cog 
    def __init__(self, bot):
        self.bot = bot

    @commands.command(help=f"Adds a name to the Secret Santa list. Usage: {PREFIX}add John Doe\n You can also mention a user or role to add them/their members.")
    #logic to determine who to add to the list based on the argument (user, role, or none)
    async def add(self, ctx, target: Union[discord.Member, discord.Role, None] = None):
        members_to_add = []
        try:
            if target is None:
                members_to_add.append(ctx.author)
                await ctx.send(f"Adding you, **{ctx.author.display_name}**...")
            elif isinstance(target, discord.Member):
                members_to_add.append(target)
                await ctx.send(f"Adding user **{target.display_name}**...")
            elif isinstance(target, discord.Role):
                role = target
                members_to_add.extend(role.members)
                if ctx.guild.me in members_to_add:
                    members_to_add.remove(ctx.guild.me)
                if not members_to_add:
                    await ctx.send(f"❌WARNING: No members found with the role **{role.name}**")
                    return
                await ctx.send(f"Adding members from role **{role.name}**...")
            else:
                await ctx.send(f"❌WARNING: Invalid argument. Please mention a user (`@user`), a role (`@role`), or use `{PREFIX} add` alone to add yourself.")
                return
        except Exception as e:
            await ctx.send(f"❌WARNING: An error occurred: {e}")
        finally:
            for i in members_to_add:
                if i.bot:
                    members_to_add.remove(i)
            await ctx.send(f"Processing {len(members_to_add)} members for addition and removing bots...")
        #logic adding people to the list and counting how many were added vs skipped 
        added_count = 0
        skipped_count = 0
        for member in members_to_add:
            user_id = member.id
            display_name = member.display_name
            if user_id in USERS_MAP.values():
                skipped_count += 1
            else:
                USERS_MAP[user_id] = display_name
                print(USERS_MAP)
                added_count += 1

        if added_count > 0:
            total_participants = len(USERS_MAP)
            await ctx.send(
                f"✅ **Addition Complete!** Added **{added_count}** new participants. "
                f"Total participants: **{total_participants}**."
            )
        elif skipped_count > 0:        
             await ctx.send(f" All {skipped_count} members from the selection were already in the list. Total participants: **{len(USERS_MAP)}**.")
        else:
            await ctx.send("No new participants were added.")


    @commands.command(help=f"Removes a name from the list. Usage: {PREFIX}remove John Doe")
    #logic for removing people from the list based on the argument (user, role, name)
    async def remove(self, ctx, *, target: Union[discord.Member,discord.Role,str, None] = None): 
        if not target:
            await ctx.send(f"❌ Please provide a name to remove. Usage: `{PREFIX}remove John Doe`")
            return

        print(target.display_name if isinstance(target, discord.Member) else None)
        if isinstance(target, discord.Role):
            memebers_to_remove = target.members
            if ctx.guild.me in memebers_to_remove:
                memebers_to_remove.remove(ctx.guild.me)
            for member in memebers_to_remove:
                if member.id in USERS_MAP.keys():
                    del USERS_MAP[member.id]
            await ctx.send(f"✅ Successfully removed all members with the role **{target.name}** from the list.")
            return
        if isinstance(target, discord.Member):
            try:
                print("removing with id")
                if target.id in USERS_MAP.keys():
                    print(f"Exact match found for ID: {target.display_name if isinstance(target, discord.Member) else None}")
                    del USERS_MAP[target.id]
                    await ctx.send(f"✅ Successfully removed **{target}** from the list.")
                    return
            except Exception as e:
                print("removing with display name")
                if target.display_name in USERS_MAP.values():
                    print(f"Exact match found for display name: {target.display_name}")
                    matched_id = next((uid for uid, name in USERS_MAP.items() if name == target.display_name), None)
                    if matched_id:
                        del USERS_MAP[matched_id]
                        await ctx.send(f"✅ Successfully removed **{target}** from the list.")
                        return
        elif isinstance(target, str):
            matched_name = match_close_name(target, USERS_MAP.values())
            if matched_name:
                matched_id = next((uid for uid, name in USERS_MAP.items() if name == matched_name), None)
                if matched_id:
                    del USERS_MAP[matched_id]
                    await ctx.send(f"✅ Successfully removed **{matched_name}** from the list (matched from input: **{target}**).")
                    return  
        else:
            await ctx.send(f"❌ Invalid argument. Please provide a valid name or mention a user to remove.")
            return
        
        
    @commands.command(help="Displays the current list of participants.")
    async def view(self, ctx):
        """Displays the current guest list."""
        if not USERS_MAP:
            await ctx.send("The Secret Santa list is currently empty.")
            return

        names_list = "\n".join([f"- {name}" for name in USERS_MAP.values()])
        await ctx.send(f"🎁 **Current Participants ({len(USERS_MAP)}):**\n{names_list}")
    
    def randomly_assign_santas(self, names_list):
        """Generates a secret santa assignment ensuring no self-assignment (Derangement)."""
        if len(names_list) < 2:
            return None 
        shuffled_names = names_list[:]
        random.shuffle(shuffled_names)
        assignments = {}
        
        for i in range(len(names_list)):
            giver = names_list[i]
            receiver = shuffled_names[i]
            while giver == receiver:
                # Re-run the assignment recursively until a valid derangement is found
                return self.randomly_assign_santas(names_list)

            assignments[giver] = receiver
        return assignments

    async def send_private_messages(self, assignments):
        for giver_name, receiver_name in assignments['assignments'].items():
            
            # Use the USERS_MAP to get the GIVER's ID from their display name
            giver_id = next((uid for uid, name in USERS_MAP.items() if name == giver_name), None)
            
            if giver_id:
                try:
                    giver_member = await self.bot.fetch_user(giver_id) 
                except discord.NotFound:
                    users_not_found.append(f"{giver_name} (ID not found)")
                    continue

                if giver_member:
                    # 2. Construct the personalized message
                    message = DM_MESSAGE_TEMPLATE.format(receiver_name=receiver_name)

                    try:
                        await giver_member.send(message)
                        Track.user_sent_to_add(giver_name)
                    except discord.Forbidden:
                        users_not_found.append(f"{giver_name} (DMs disabled)")
                    except Exception as e:
                        users_not_found.append(f"{giver_name} (Error: {e})")
            else:
                users_not_found.append(f"{giver_name} (ID missing from map)")
                
        return users_sent_to, users_not_found

    @commands.command(help="Generates assignments and sends DMs to participants.")
    async def assign(self, ctx):
        """Handles the full assignment and DM distribution process."""
        users_sent=0
        users_failed=0
        if len(USERS_MAP) < 2:
            await ctx.send("❌ Cannot run assignment: Need at least 2 names to assign Secret Santas. Use `SS!add`.")
            return
        assignments = self.randomly_assign_santas(list(USERS_MAP.values()))
        if not assignments:
            await ctx.send("❌ Error generating assignments. Please make sure there are over 2 participants in the list. current number of participants: " + str(len(USERS_MAP)))
            
        # Package assignments with guild ID for DM sending
        dm_data = {
            'assignments': assignments,
            'ctx_guild_id': ctx.guild.id
        }

        # Send Private Messages
        users_sent, users_failed = await self.send_private_messages(dm_data)
        
        sent_msg = f"✅ **DMs Sent Successfully:** {len(Track.user_sent_to_add)} participants received their assignments."
        if users_failed:
            sent_msg += f"\n⚠️ **DM Failures:** {len(users_failed)}: {', '.join(users_failed)}"
            
        await ctx.send(sent_msg)

# --- BOT INITIALIZATION ---

# Setting up Discord intents 
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.members = True 
print(intents.value)

def get_prefix(bot, message):
    prefix = PREFIX
    if message.content.lower().startswith(prefix.lower()):
        return message.content[: len(prefix)]
    return prefix

# Initialize the Bot with the correct prefix and intents
bot = commands.Bot( command_prefix=get_prefix, intents=intents, strip_after_prefix=True)


if __name__ == "main":
    bot = commands.Bot( command_prefix=get_prefix, intents=intents, strip_after_prefix=True)
    Track = Tracker()
@bot.event
async def on_ready():
    """Confirms the bot is logged in and ready."""
    print(f'✅ Logged in as {bot.user}!')
    await bot.add_cog(SantaCommands(bot))
    print(f'✅ Loaded SantaCommands cog.')

if DISCORD_TOKEN:
    try:
        bot.run(DISCORD_TOKEN)
    except discord.errors.LoginFailure:
        print("\nFATAL ERROR: Failed to log in. Check your DISCORD_TOKEN.")
else:
    print("\nFATAL ERROR: DISCORD_TOKEN not found")
