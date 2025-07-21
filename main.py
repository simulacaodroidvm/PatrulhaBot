import discord
from discord.ext import commands, tasks
from discord.ui import View, Button
from datetime import datetime, timedelta, time as dtime
from keep_alive import keep_alive
import pytz, json, os

TOKEN = 'TOKEN'  # Substitua pelo seu token
CANAL_LOGS_ID = 1395842082790179036  # Substitua pelo ID do canal de logs
CANAL_RANKING_ID = 1395952949938622464  # Substitua pelo ID do canal de ranking
ARQUIVO_DADOS = 'dados.json'
BRASIL_TZ = pytz.timezone("America/Sao_Paulo")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# Funções utilitárias
def carregar_dados():
    if not os.path.exists(ARQUIVO_DADOS):
        return {}
    with open(ARQUIVO_DADOS, "r") as f:
        return json.load(f)

def salvar_dados(dados):
    with open(ARQUIVO_DADOS, "w") as f:
        json.dump(dados, f, indent=4)

# View com botões
class PainelPatrulha(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📍 Iniciar Patrulha", style=discord.ButtonStyle.success, custom_id="btn_start")
    async def iniciar(self, interaction: discord.Interaction, button: Button):
        cargo_eb = discord.utils.get(interaction.user.roles, name="👮 ⌜EB⌟")
        if not cargo_eb:
            await interaction.response.send_message("❌ Você não tem permissão para iniciar patrulha.", ephemeral=True)
            return

        dados = carregar_dados()
        user_id = str(interaction.user.id)
        agora = datetime.now(BRASIL_TZ)

        if user_id in dados and "entrada" in dados[user_id]:
            await interaction.response.send_message("❌ Você já iniciou uma patrulha!", ephemeral=True)
            return

        dados[user_id] = {
            "entrada": agora.isoformat(),
            "horas": dados.get(user_id, {}).get("horas", 0),
            "nome": interaction.user.name
        }
        salvar_dados(dados)

        embed = discord.Embed(title="🚨 Patrulha Iniciada", description=f"{interaction.user.mention} iniciou a patrulha.", color=discord.Color.green())
        embed.add_field(name="🕒 Horário", value=agora.strftime("%H:%M:%S - %d/%m/%Y"))
        await interaction.response.send_message(embed=embed)

        canal_logs = bot.get_channel(CANAL_LOGS_ID)
        if canal_logs:
            await canal_logs.send(f"🚨 Patrulha iniciada por {interaction.user.mention} às {agora.strftime('%H:%M:%S - %d/%m/%Y')}")

    @discord.ui.button(label="✅ Finalizar Patrulha", style=discord.ButtonStyle.danger, custom_id="btn_stop")
    async def finalizar(self, interaction: discord.Interaction, button: Button):
        dados = carregar_dados()
        user_id = str(interaction.user.id)
        agora = datetime.now(BRASIL_TZ)
        cargo_resp = discord.utils.get(interaction.user.roles, name="•「  Resp. Bate-Ponto 」•")

        if user_id in dados and "entrada" in dados[user_id]:
            entrada = datetime.fromisoformat(dados[user_id]["entrada"])
        elif cargo_resp:
            entrada = agora - timedelta(minutes=1)
        else:
            await interaction.response.send_message("❌ Você não iniciou uma patrulha!", ephemeral=True)
            return

        tempo = (agora - entrada).total_seconds() / 3600
        tempo = round(tempo, 2)

        # ✅ Solução para evitar KeyError
        if user_id not in dados:
            dados[user_id] = {}

        dados[user_id]["horas"] = dados[user_id].get("horas", 0) + tempo

        # 🔁 Remove a entrada da patrulha após finalizar
        if "entrada" in dados[user_id]:
            del dados[user_id]["entrada"]

        salvar_dados(dados)

        embed = discord.Embed(
            title="📄 Patrulha Finalizada",
            description=f"{interaction.user.mention} finalizou a patrulha.",
            color=discord.Color.red()
        )
        embed.add_field(name="⏰ Tempo de patrulha", value=f"{tempo:.2f} horas", inline=False)
        await interaction.response.send_message(embed=embed)

        canal_logs = bot.get_channel(CANAL_LOGS_ID)
        if canal_logs:
            await canal_logs.send(f"📄 Patrulha finalizada por {interaction.user.mention} às {agora.strftime('%H:%M:%S - %d/%m/%Y')}")

        try:
            await interaction.message.edit(view=None)
        except:
            pass

# Comando para mostrar painel
@bot.command(name="painel")
async def painel(ctx):
    await ctx.send("Clique em um botão para registrar sua patrulha:", view=PainelPatrulha())

# Comando !horas
@bot.command(name="horas")
async def mostrar_horas(ctx):
    dados = carregar_dados()
    user_id = str(ctx.author.id)
    horas = dados.get(user_id, {}).get("horas", 0)
    await ctx.send(f"⏱️ {ctx.author.mention}, você tem **{horas:.2f} horas** de patrulha.")

# Comando !ranking
@bot.command(name="ranking")
async def ranking(ctx):
        dados = carregar_dados()

        if not dados:
            await ctx.send("📊 Nenhum dado de patrulha encontrado.")
            return

        membros = []
        for user_id, info in dados.items():
            horas = info.get("horas", 0)
            membro = ctx.guild.get_member(int(user_id))
            nome = membro.display_name if membro else f"ID {user_id}"
            membros.append((nome, horas))

        membros.sort(key=lambda x: x[1], reverse=True)

        ranking_texto = "**🏆 Ranking de Patrulha:**\n\n"
        for i, (nome, horas) in enumerate(membros[:10], start=1):
            ranking_texto += f"**{i}.** {nome} — `{horas:.2f}` horas\n"

        canal_ranking = bot.get_channel(1395952949938622464)
        if canal_ranking:
            await canal_ranking.send(ranking_texto)
        else:
            await ctx.send("❌ Não foi possível encontrar o canal de ranking.")
    # === keep_alive.py ===
from flask import Flask
from threading import Thread
import os

app = Flask('')

@app.route('/')
def home():
        return "✅ Bot está online!"

def run():
        port = int(os.environ.get("PORT", 5000))  # Deixa o Replit escolher a porta
        app.run(host='0.0.0.0', port=port)

def keep_alive():
        t = Thread(target=run)
        t.start()

# Reset semanal
@tasks.loop(time=dtime(hour=0, minute=0, tzinfo=BRASIL_TZ))
async def resetar_horas():
    dados = carregar_dados()
    for user in dados:
        dados[user]["horas"] = 0
        dados[user].pop("entrada", None)
    salvar_dados(dados)

    canal = bot.get_channel(CANAL_LOGS_ID)
    if canal:
        await canal.send("🔁 As horas de patrulha foram resetadas automaticamente (semanalmente).")

@bot.event
async def on_ready():
    bot.add_view(PainelPatrulha())
    resetar_horas.start()
    print(f"✅ Bot conectado como {bot.user}")

keep_alive()
bot.run("TOKEN")