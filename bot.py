####
# backend: https://github.com/scooredmars
# front: toma5z-js


from discord.ext import commands, ipc
from decouple import config
import discord

class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ipc = ipc.Server(self, secret_key=config("IPC_KEY"))

    async def on_ready(self):
        """Called upon the READY event"""
        print("Bot is ready.")

    async def on_ipc_ready(self):
        """Called upon the IPC Server being ready"""
        print("Ipc is ready.")

    async def on_ipc_error(self, endpoint, error):
        """Called upon an error being raised within an IPC route"""
        print(endpoint, "raised", error)

my_bot = MyBot(command_prefix=">", intents=discord.Intents.all())

@my_bot.ipc.route()
async def send_embed(data):
    guild = my_bot.get_guild(int(config("APPLICATION_GUILD_ID")))
    channel = discord.utils.get(guild.channels, id=int(config("CHANNEL_APPLICATION_ID")))

    embedVar = discord.Embed(title=data.user_name, color=0x3498db)
    for element in data.form_values.items():
        embedVar.add_field(name=element[0], value=element[1], inline=False)

    await channel.send(embed=embedVar)

    return True

if __name__ == "__main__":
    my_bot.ipc.start()
    my_bot.run(config("TOKEN"))