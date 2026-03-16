import os
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")


@bot.command(name="ping")
async def ping(ctx):
    """Check the bot's latency."""
    latency = bot.latency
    if latency is None:
        await ctx.send("Pong! Latency: N/A")
    else:
        await ctx.send(f"Pong! Latency: {round(latency * 1000)}ms")


@bot.command(name="hello")
async def hello(ctx):
    """Say hello."""
    await ctx.send(f"Hello, {ctx.author.mention}!")


if __name__ == "__main__":
    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        raise ValueError(
            "DISCORD_TOKEN environment variable is not set. "
            "See the README for setup instructions."
        )
    bot.run(token)
