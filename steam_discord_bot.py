import discord
import time
import os
from dotenv import load_dotenv
from discord.ext import commands, tasks
from selenium import webdriver
from bs4 import BeautifulSoup
from datetime import datetime

#Loading local enviroment
load_dotenv()

#Setting up
client = commands.Bot(command_prefix="!", intents=discord.Intents.all())
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
steam_link = None
len_of_arrays, copies_of_lists, copies_of_img = [], [], []

#Function to parse info from the steam link, and give it back
def checking_achievements(profile_link):
    #Setting up
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--lang=en-US")
    driver = webdriver.Chrome(options=options)
    driver.get(url=profile_link)
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, features="lxml")
    time.sleep(3)
    #Parsing info about achievements
    achievements = soup.find_all(name="h3", class_="ellipsis")
    #Getting names of achievements
    achievements_text = [x.text for x in achievements]
    #Getting the time when the achievement was got
    time_unlocked = soup.find_all(name='div', class_='achieveUnlockTime')
    time_unlocked_text = [x.text for x in time_unlocked]
    #Creating a list of achievements wich was UNLOCKED, by finding the len of unlocked time (text) and creating a list
    unlocked_achievements = achievements_text[0:len(time_unlocked)]
    divs = soup.find_all(name="div", class_='achieveImgHolder')
    #Parsing the image links of achievements
    img_links = [x['src'] for div in divs for x in div.find_all(name='img')]
    #Creating a list of image links of UNLOCKED achievements
    unlocked_img_links = img_links[0:len(time_unlocked)]
    #Creating a list to see all info (optional)
    stuff = [f"Achievement {x}, IMG: {link}" for x, link in zip(unlocked_achievements, unlocked_img_links)]
    #Getting the steam nickname of profile
    steam_nickname_element = soup.find(name="a", class_="whiteLink persona_name_text_content")
    if steam_nickname_element:
        steam_nickname = steam_nickname_element.text
    else:
        steam_nickname = "Unknown Player"
    try:
        #Getting the profile image
        try:
            steam_profile_img = soup.find(name='div', class_="playerAvatar medium in-game").find(name="img")["src"]
        except AttributeError:
            steam_profile_img = soup.find(name='div', class_="playerAvatar medium online").find(name="img")["src"]
    except AttributeError:
        steam_profile_img = soup.find(name='div', class_="playerAvatar medium offline").find(name="img")["src"]
    #Returning all info we got
    return time_unlocked_text, unlocked_achievements, unlocked_img_links, steam_nickname, steam_profile_img

#Creating an event when the bot is ready
@client.event
async def on_ready():
    print("I'm ready!")

#This is a test command so that people can see the example message of how the notify will look
@client.command()
async def example(ctx, arg):
    link = arg
    time_unlocked, unlocked_achievements, img_links, steam_nickname, steam_profile_img = (
        checking_achievements(link))
    embed = discord.Embed(description=f"Steam achievement announcement: {unlocked_achievements[0]}",
                          color=discord.Color.green(),
                          timestamp=datetime.utcnow())
    embed.set_author(name=f"{steam_nickname}", icon_url=f"{steam_profile_img}")
    embed.set_thumbnail(url=img_links[0])
    await ctx.send(embed=embed)

#Creating command to get the url, and returning it and starting the task_track_achievements()
@client.command()
async def track_achievements(ctx, arg):
    global steam_link
    steam_link = arg
    if "achievements" in arg:
        await ctx.send("Successfully linked your profile's achievements!")
        task_track_achievements.start()
    else:
        await ctx.send("Something went wrong, please recheck your URL!")

#Creating a main task to track achievements
@tasks.loop(seconds=60)
async def task_track_achievements():
    #Getting our variables
    global steam_link, len_of_arrays, copies_of_lists, copies_of_img
    channel = client.get_channel(1195689857423523862)
    #Getting our data from the first func
    time_unlocked, unlocked_achievements, img_links, steam_nickname, steam_profile_img = (
        checking_achievements(steam_link))
    x = len(unlocked_achievements)
    #Checking if lists are empty then adding the first data
    if len(copies_of_img) == 0:
        for item in img_links:
            copies_of_img.append(item)
    if len(copies_of_lists) == 0:
        for item in unlocked_achievements:
            copies_of_lists.append(item)
    if len(len_of_arrays) == 0:
        len_of_arrays.append(x)
    print(f"Current copies of images: {copies_of_img}\n"
          f"Current copies of achievements: {copies_of_lists}\n"
          f"Len of array: {len_of_arrays}")
    #Checking if the current len is different from the first one than we doing else statement
    if x in len_of_arrays:
        print("No new achievements")
    else:
        for achievement, image_link in zip(unlocked_achievements, img_links):
            if achievement not in copies_of_lists and image_link not in copies_of_img:
                copies_of_lists.append(achievement)
                copies_of_img.append(image_link)
                len_of_arrays.append(len(unlocked_achievements))
                print(f"New copies of achievements: {copies_of_lists}\n"
                      f"New copies of images: {copies_of_img}")
                #Creating an embed with all our data and then sending it
                embed = discord.Embed(description=f"Steam achievement announcement: {achievement}",
                                      color=discord.Color.green(),
                                      timestamp=datetime.utcnow())
                embed.set_author(name=f"{steam_nickname}", icon_url=f"{steam_profile_img}")
                embed.set_thumbnail(url=image_link)
                await channel.send(embed=embed)

client.run(DISCORD_TOKEN)
