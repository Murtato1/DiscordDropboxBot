import os
import random
import discord
import dropbox
import pathlib
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from dotenv import load_dotenv
from discord.ext import commands
from dropbox.exceptions import AuthError

# Input all discord API requirements below
# You might need to change intents if you plan on altering the code
TOKEN = "YOUR TOKEN HERE"
GUILD = "YOUR GUILD ID HERE"
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
load_dotenv()
bot = commands.Bot(command_prefix="PREFIX HERE", intents=intents)

# Enter the dropbox token from the API below
DROPBOX_ACCESS_TOKEN = 'ENTER DB TOKEN'

# All three paths below must be to different folders

# The below path should be where images are saved before sending back
local_file_path = r'PATH WHERE IMAGES SHOULD BE SAVED' + 'img.png'

# The below path should be where images are saved before uploading
upload_path = r'PATH WHERE IMAGES SHOULD BE SAVED' + 'img.png'

# The below path should be where images are saved before editing
presave_path = r'PATH WHERE IMAGES SHOULD BE SAVED' + 'img.png'

# Below are methods to interact with dropbox

def dropbox_connect():
    # Tries to establish a connection based on the given token
    try:
        dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
    except AuthError as e:
        print('Error connecting to Dropbox with access token: ' + str(e))
    return dbx

def dropbox_upload():

    try:
        dbx = dropbox_connect()
        db_path = dbx.files_list_folder('', recursive=True).entries[0].path_display

        local_path = pathlib.Path(upload_path)

        # Will upload the file in the upload path to the db folder
        with local_path.open("rb") as f:
            meta = dbx.files_upload(f.read(), db_path, mode=dropbox.files.WriteMode("overwrite"))
            return meta

    except Exception as e:
        print('Error uploading file to Dropbox: ' + str(e))

def dropbox_download():
    dbx = dropbox_connect()
    file_list = []

    update_list(dbx, file_list)

    # Will send a random image from the list of files in db
    with open(presave_path, "wb") as f:
        f.write(random.choice(file_list).content)

def image_edit(arg):
# Uses pillow to caption the image and send it

    # Saves the image that was downloaded
    img = Image.open(presave_path)
    if os.stat(presave_path).st_size > 8205695:
        # Resizes image if it is too large for discord
        img = img.resize((800, 800))
        img.save("img.png", quality=1)

    # Gets the size of the image
    I1 = ImageDraw.Draw(img)
    with open("img.png", 'rb'):
        width, height = img.size

    position = (0, 0)

    # Captions the image, scaling letters based on image size
    # A white box is added behind the text for readability
    myFont = ImageFont.truetype(r'PATH YOUR DESIRED .ttf FILE', round(width / 16 + height / 16))
    bbox = I1.textbbox(position, arg, font=myFont)
    I1.rectangle(bbox, fill="white")
    I1.text(position, arg, font=myFont, fill="black")

    # Image is saved to project folder
    img.save("img.png", optimize=True)

def update_list(dbx, file_list):
# Helper method for download method
    #Puts all dropbox entries in a list
    for entry in dbx.files_list_folder('', recursive=True).entries:
        if isinstance(entry, dropbox.files.FileMetadata):
            file_list += dbx.files_download(entry.path_display)

# Below are the discord commands that can be called by the bot

@commands.command(name='send')
async def send_caption(message, *, arg):
# Downloads a random image from dropbox, adds the caption given, and sends
    dropbox_download()
    image_edit(arg)
    with open("img.png", 'rb') as f:
        picture = discord.File(f)
        await message.send(file=picture)

@commands.command(name='upload')
async def upload(ctx):
# Downloads the attachment and then uploads it to db
    for attachment in ctx.message.attachments:
        await attachment.save(upload_path)
    dropbox_upload()

# All commands are added and the bot is run below

bot.add_command(send_caption)
bot.add_command(upload)
bot.run(TOKEN)