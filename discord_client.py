import discord
from discord.ext import commands, tasks
from datetime import datetime
from agents.orchestrator import news_graph
from config import DISCORD_TOKEN, MORNING_HOUR, EVENING_HOUR
from discord import Embed, Color
import json
import os

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ID del canale configurato correttamente
NEWS_CHANNEL_ID = 1497874759893913620

@bot.event
async def on_ready():
    print(f"{bot.user} is now running!")
    if not generate_digest_task.is_running():
        generate_digest_task.start()

def save_news_for_web(summaries):
    """Salva le ultime notizie in un file JSON per la landing page"""
    try:
        web_folder = "web"
        if not os.path.exists(web_folder):
            os.makedirs(web_folder)
        
        file_path = os.path.join(web_folder, "news.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(summaries, f, ensure_ascii=False, indent=4)
        print(f"✅ Database web aggiornato: {file_path}")
    except Exception as e:
        print(f"❌ Errore nel salvataggio web: {e}")

async def create_professional_embed(summaries):
    """Crea un unico Embed compatto e professionale per tutte le news"""
    embed = Embed(
        title="⚡ Graphyte Tech & AI Digest",
        description=f"Le notizie più rilevanti selezionate per te.\n*{datetime.now().strftime('%A %d %B %Y')}*",
        color=Color.from_rgb(0, 255, 255)  # Ciano Graphyte
    )
    
    for i, summary in enumerate(summaries[:8], 1):
        # Tronca il riassunto se troppo lungo
        clean_summary = summary['summary'][:300] + "..." if len(summary['summary']) > 300 else summary['summary']
        
        field_value = f"{clean_summary}\n🔗 [Leggi di più]({summary['url']})"
        embed.add_field(
            name=f"{i}. {summary['title'][:256]}",
            value=field_value,
            inline=False
        )
    
    # Brand identity nel footer
    embed.set_footer(
        text="Powered by Graphyte Logic • AI Newsroom", 
        icon_url="https://github.com/graphyte-logic.png"
    )
    return embed

@tasks.loop(hours=1)
async def generate_digest_task():
    """Check automatico per l'invio programmato"""
    if NEWS_CHANNEL_ID is None:
        return
    
    now = datetime.now().hour
    if now == MORNING_HOUR or now == EVENING_HOUR:
        try:
            print(f"Generating scheduled digest at {datetime.now()}")
            state = {"articles": [], "summaries": [], "digest": ""}
            result = news_graph.invoke(state)
            summaries = result.get("summaries", [])
            
            channel = bot.get_channel(NEWS_CHANNEL_ID)
            if channel and summaries:
                # Salva per il web prima di inviare
                save_news_for_web(summaries)
                
                embed = await create_professional_embed(summaries)
                await channel.send(embed=embed)
                print("Scheduled digest posted!")
        except Exception as e:
            print(f"Error in scheduled digest: {e}")

@bot.command()
async def digest(ctx):
    """Comando manuale !digest per attivare il bot"""
    try:
        await ctx.send("🔍 Recupero e riassumo le ultime notizie tech...")
        
        state = {"articles": [], "summaries": [], "digest": ""}
        result = news_graph.invoke(state)
        summaries = result.get("summaries", [])
        
        if not summaries:
            return await ctx.send("📭 Nessuna notizia rilevante trovata al momento.")

        # Aggiorna il file JSON per il sito web
        save_news_for_web(summaries)

        # Invia l'embed su Discord
        embed = await create_professional_embed(summaries)
        await ctx.send(embed=embed)
            
    except Exception as e:
        await ctx.send(f"❌ Errore durante la generazione: {str(e)}")

def run():
    bot.run(DISCORD_TOKEN)