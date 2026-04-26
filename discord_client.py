import discord
from discord.ext import commands, tasks
from datetime import datetime
from agents.orchestrator import news_graph
from config import DISCORD_TOKEN, MORNING_HOUR, EVENING_HOUR

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Set this after creating Discord server
NEWS_CHANNEL_ID = 1497874759893913620

@bot.event
async def on_ready():
    print(f"{bot.user} is now running!")
    if not generate_digest_task.is_running():
        generate_digest_task.start()

@tasks.loop(hours=1)
async def generate_digest_task():
    """Check every hour if it's time to post"""
    if NEWS_CHANNEL_ID is None:
        return
    
    now = datetime.now().hour
    
    if now == MORNING_HOUR or now == EVENING_HOUR:
        try:
            print(f"Generating digest at {datetime.now()}")
            
            # Generate digest
            state = {"articles": [], "summaries": [], "digest": ""}
            result = news_graph.invoke(state)
            digest = result.get("digest", "No news today.")
            
            # Post to Discord
            channel = bot.get_channel(NEWS_CHANNEL_ID)
            if channel:
                # Discord message limit: 2000 chars
                if len(digest) > 1900:
                    chunks = [digest[i:i+1900] for i in range(0, len(digest), 1900)]
                    for chunk in chunks:
                        await channel.send(chunk)
                else:
                    await channel.send(digest)
                print("Digest posted!")
            else:
                print(f"Channel {NEWS_CHANNEL_ID} not found")
        except Exception as e:
            print(f"Error generating digest: {e}")

@bot.command()
async def digest(ctx):
    """Manual trigger - type !digest in Discord"""
    try:
        state = {"articles": [], "summaries": [], "digest": ""}
        result = news_graph.invoke(state)
        summaries = result.get("summaries", [])
        
        # Header embed
        from discord import Embed, Color
        from datetime import datetime
        
        embeds = []
        
        # Main header
        header = Embed(
            title="🤖 Tech & AI Digest",
            description=datetime.now().strftime('%A %d %B %Y'),
            color=Color.blue()
        )
        embeds.append(header)
        
        # Article embeds
        for i, summary in enumerate(summaries[:8], 1):
            embed = Embed(
                title=f"{i}. {summary['title'][:256]}",
                description=summary['summary'][:2048],
                url=summary['url'],
                color=Color.from_rgb(88, 166, 255)
            )
            embed.set_footer(text=f"📰 {summary['source']}")
            embeds.append(embed)
        
        # Send all embeds
        for embed in embeds:
            await ctx.send(embed=embed)
            
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

def run():
    bot.run(DISCORD_TOKEN)