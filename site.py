'''
BackEnd Created by ScooredMars
https://github.com/scooredmars
'''

from quart_discord import DiscordOAuth2Session, requires_authorization, Unauthorized
from quart import Quart, render_template, redirect, url_for, request, flash
from discord.ext import ipc
from decouple import config
import datetime, sqlite3
from datetime import datetime as dt

app = Quart(__name__)
ipc_client = ipc.Client(
    secret_key=config("IPC_KEY")
)

app.config["SECRET_KEY"] = config("SECRET_KEY")
app.config["DISCORD_CLIENT_ID"] = config("DISCORD_CLIENT_ID")
app.config["DISCORD_CLIENT_SECRET"] = config("DISCORD_CLIENT_SECRET")
app.config["DISCORD_REDIRECT_URI"] = config("DISCORD_REDIRECT_URI")
app.config["DISCORD_BOT_TOKEN"] = config("TOKEN")
app.permanent_session_lifetime = datetime.timedelta(minutes=60)

dc = DiscordOAuth2Session(app)

@app.route("/login/")
async def login():
    return await dc.create_session()

@app.route("/callback")
async def callback():
    try:
        await dc.callback()
    except Exception:
        pass

    return redirect(url_for("home"))

@app.errorhandler(Unauthorized)
async def redirect_unauthorized(e):
    return redirect(url_for("login"))

@app.route("/")
async def home():
    if await dc.authorized:
        user = await dc.fetch_user()
        user_guilds = await dc.fetch_guilds()

        user_exist_on_server = False

        user_id = user.id
        for guild in user_guilds:
            if guild.id == config("MAIN_GUILD_ID"):
                user_exist_on_server = True

        return await render_template("home.html", authorized=await dc.authorized, user_id=user_id, user_exist_on_server=user_exist_on_server)
    else:
        return await render_template("home.html", authorized=await dc.authorized)

@app.route("/statute")
async def statute():
    return await render_template("statute.html", authorized=await dc.authorized)

@app.route("/podania", methods=["GET", "POST"])
@requires_authorization
async def application():
    user = await dc.fetch_user()

    user_exist = False
    embed_can_be_sended = False

    conn = sqlite3.connect('users.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS USERS
        (ID INTEGER PRIMARY KEY AUTOINCREMENT,
        CLIENT_ID INTEGER NOT NULL,
        LAST_FORM_SUBMISSION DATETIME NOT NULL,
        UNIQUE(CLIENT_ID));''')

    today = datetime.datetime.now()
    cursor = conn.execute("SELECT ID, CLIENT_ID, LAST_FORM_SUBMISSION FROM USERS")

    for row in cursor:
        if int(row[1]) == int(user.id):
            user_exist = True
            date_of_user_last_message = row[2]
            user_db_id = row[0]
            break

    if user_exist:
        date_difference = today - dt.strptime(date_of_user_last_message, '%Y-%m-%d %H:%M:%S.%f')
        if date_difference.days >= 5:
            embed_can_be_sended = True
    else:
        embed_can_be_sended = True

    if request.method == "POST":
        form = await request.form
        if form:
            form_values = {}
            error = None
            embed_send = None
            for element in form:
                if form[element] == '':
                    error = "Nie wypełniono pola !"
                    break
                else:
                    form_values[element] = form[element]

            if error == None:
                if embed_can_be_sended:
                    embed_send = await ipc_client.request("send_embed", user_name=str(user), form_values=form_values)
                    if embed_send:
                        if not user_exist:
                            conn.execute("INSERT INTO USERS (CLIENT_ID, LAST_FORM_SUBMISSION) VALUES (?, ?)", (user.id, today))
                            conn.commit()
                        else:
                            conn.execute("UPDATE USERS set LAST_FORM_SUBMISSION = ? where ID = ?", (today, user_db_id))
                            conn.commit()

            conn.close()
            await flash('Zgłoszenie zostało wysłane')
            return redirect(url_for("application", error=error))
    else:
        user = await dc.fetch_user()
        conn.close()
        return await render_template("application.html", authorized=await dc.authorized, user=user, embed_can_be_sended=embed_can_be_sended)

if __name__ == "__main__":
    app.run(debug=false)