import discord
from discord.ext import commands, tasks
from datetime import datetime
from agents.orchestrator import news_graph
from config import DISCORD_TOKEN, MORNING_HOUR, EVENING_HOUR, LEGAL_CHANNEL_ID, FONTI_LEGAL
from discord import Embed, Color
import json
import subprocess

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Id del canale Discord per le news Tech
NEWS_CHANNEL_ID = 1497874759893913620

def auto_push_to_github(filename):
    """Invia automaticamente il file modificato (json) su GitHub Pages"""
    try:
        subprocess.run(["git", "add", filename], check=True)
        subprocess.run(["git", "commit", "-m", f"⚡ Auto-update {filename}: {datetime.now().strftime('%H:%M:%S')}"], check=True)
        subprocess.run(["git", "push", "origin", "master"], check=True)
        print(f"🚀 [GitHub] {filename} pubblicato con successo nella Root!")
    except Exception as e:
        print(f"⚠️ [Git Error] Impossibile aggiornare GitHub per {filename}: {e}")

def save_news_for_web(summaries, filename):
    """Salva il file JSON specificato nella cartella principale e avvia il push"""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(summaries, f, ensure_ascii=False, indent=4)
        
        print(f"✅ Database web aggiornato: {filename}")
        auto_push_to_github(filename)
    except Exception as e:
        print(f"❌ Errore salvataggio file web ({filename}): {e}")

@bot.event
async def on_ready():
    print(f"Starting AI Newsroom Multi-Ramo...")
    print(f"{bot.user} is now running!")

# --- COMANDO TECH (GIA' ESISTENTE) ---
@bot.command()
async def digest(ctx):
    """Trigger manuale per il ramo tecnologico"""
    try:
        await ctx.send("🔍 Analisi del web in corso per Graphyte Tech...")
        
        # Facciamo partire il grafo passandogli nel contesto che vogliamo news Tech
        state = {"articles": [], "summaries": [], "digest": "", "category": "tech"}
        result = news_graph.invoke(state)
        summaries = result.get("summaries", [])
        
        if summaries:
            save_news_for_web(summaries, "news.json")
            
            header = Embed(
                title="🤖 Tech & AI Digest",
                description=datetime.now().strftime('%A %d %B %Y'),
                color=Color.blue()
            )
            await ctx.send(embed=header)
            
            for i, summary in enumerate(summaries[:8], 1):
                embed = Embed(
                    title=f"{i}. {summary['title'][:256]}",
                    description=summary['summary'][:2048],
                    url=summary['url'],
                    color=Color.from_rgb(88, 166, 255)
                )
                embed.set_footer(text=f"📰 {summary['source']}")
                await ctx.send(embed=embed)
        else:
            await ctx.send("📭 Nessun aggiornamento tecnologico trovato.")
    except Exception as e:
        await ctx.send(f"❌ Errore durante il digest tech: {str(e)}")

# --- NUOVO COMANDO LEGAL ---
@bot.command()
async def legal(ctx):
    """Trigger manuale per il ramo legale"""
    try:
        await ctx.send("⚖️ Consultazione degli archivi giuridici in corso per Graphyte Legal...")
        
        # Passiamo "legal" nell'invocazione del grafo
        state = {"articles": [], "summaries": [], "digest": "", "category": "legal"}
        result = news_graph.invoke(state)
        summaries = result.get("summaries", [])
        
        if summaries:
            # Salviamo nel nuovo file dedicato
            save_news_for_web(summaries, "legal_news.json")
            
            header = Embed(
                title="⚖️ Legal & Diritto Intelligence",
                description=datetime.now().strftime('%A %d %B %Y'),
                color=Color.from_rgb(255, 170, 0) # Colore Oro/Ambra coerente con il sito!
            )
            await ctx.send(embed=header)
            
            for i, summary in enumerate(summaries[:8], 1):
                embed = Embed(
                    title=f"{i}. {summary['title'][:256]}",
                    description=summary['summary'][:2048],
                    url=summary['url'],
                    color=Color.from_rgb(255, 170, 0)
                )
                embed.set_footer(text=f"📰 {summary['source'] || 'Fonte Giuridica'}")
                await ctx.send(embed=embed)
        else:
            await ctx.send("📭 Nessun aggiornamento legale rilevante trovato.")
    except Exception as e:
        await ctx.send(f"❌ Errore durante il digest legal: {str(e)}")

def run():
    bot.run(DISCORD_TOKEN)