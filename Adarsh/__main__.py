import os
import sys
import glob
import asyncio
import logging
import importlib
from pathlib import Path
from pyrogram import idle, Client
from .bot import StreamBot
from .vars import Var
from aiohttp import web
from .server import web_server
from .utils.keepalive import ping_server
from Adarsh.bot.clients import initialize_clients
import ntplib
from time import ctime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logging.getLogger("aiohttp").setLevel(logging.ERROR)
logging.getLogger("pyrogram").setLevel(logging.ERROR)

ppath = "Adarsh/bot/plugins/*.py"
files = glob.glob(ppath)

loop = asyncio.get_event_loop()

async def synchronize_time():
    try:
        client = ntplib.NTPClient()
        response = client.request('pool.ntp.org')
        ntp_time = ctime(response.tx_time)
        system_time = ctime()
        time_difference = abs(response.tx_time - time.time())
        if time_difference > 60:
            logging.error(f"Time difference too high: {time_difference} seconds. Syncing system time...")
            raise Exception("System time is out of sync with NTP server.")
        logging.info(f"System time synchronized: {system_time} vs {ntp_time}")
    except Exception as e:
        logging.error(f"Failed to synchronize time: {e}")
        sys.exit(1)

async def start_services():
    await synchronize_time()
    
    print('\n')
    print('------------------- Initializing Telegram Bot -------------------')
    await StreamBot.start()
    bot_info = await StreamBot.get_me()
    StreamBot.username = bot_info.username
    print("------------------------------ DONE ------------------------------")
    print()
    print(
        "---------------------- Initializing Clients ----------------------"
    )
    await initialize_clients()
    print("------------------------------ DONE ------------------------------")
    print('\n')
    print('--------------------------- Importing ---------------------------')
    for name in files:
        with open(name) as a:
            patt = Path(a.name)
            plugin_name = patt.stem.replace(".py", "")
            plugins_dir = Path(f"Adarsh/bot/plugins/{plugin_name}.py")
            import_path = ".plugins.{}".format(plugin_name)
            spec = importlib.util.spec_from_file_location(import_path, plugins_dir)
            load = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(load)
            sys.modules["Adarsh.bot.plugins." + plugin_name] = load
            print("Imported => " + plugin_name)
    if Var.ON_HEROKU:
        print("------------------ Starting Keep Alive Service ------------------")
        print()
        asyncio.create_task(ping_server())
    print('-------------------- Initializing Web Server --------------------')
    app = web.AppRunner(await web_server())
    await app.setup()
    bind_address = "0.0.0.0" if Var.ON_HEROKU else Var.BIND_ADDRESS
    await web.TCPSite(app, bind_address, Var.PORT).start()
    print('----------------------------- DONE ------------------------------')
    print('\n')
    print('---------------------------------------------------------------------------------------------------------')
    print(' follow me for more such exciting bots! https://github.com/adarsh-goel')
    print('---------------------------------------------------------------------------------------------------------')
    print('\n')
    print('----------------------- Service Started --------------------------')
    print('                        bot =>> {}'.format((await StreamBot.get_me()).first_name))
    print('                        server ip =>> {}:{}'.format(bind_address, Var.PORT))
    print('                        Owner =>> {}'.format((Var.OWNER_USERNAME)))
    if Var.ON_HEROKU:
        print('                        app running on =>> {}'.format(Var.FQDN))
    print('---------------------------------------------------------------------------------------------------------')
    print('Give a star to my repo https://github.com/adarsh-goel/filestreambot-pro also follow me for new bots')
    print('---------------------------------------------------------------------------------------------------------')
    await idle()

if __name__ == '__main__':
    try:
        loop.run_until_complete(start_services())
    except KeyboardInterrupt:
        logging.info('----------------------- Service Stopped -----------------------')
