#!/usr/bin/python
# Import pycord Library
import discord
from discord.ext import commands
# Import Built in Libraries
import time
import subprocess as sp
# Import Custom modules used to define markdown and configuration
import dsformat as dsf
import botconfig as conf
# Create intents object for the bot
intents=discord.Intents.default()
intents.members=True
# Create Bot Object using prefix commands
bot=commands.Bot(command_prefix=conf.prefix,owner_id=conf.owner,intents=intents)
# Unused Currently
activities=["Awaiting Input","Processing","Querying Database","Error"]
activity=0
# Empty Globals used in on_ready
starttime=0
guilds=[]
channels=[]
roles=[]
features=[]
# END VARIABLE DEFINITIONS

# Function to make a MySQL style table out of a list of lists
def convtable(list):
	# Column Width List (Filled out later)
    colsize=[0,0,0,0,0]
    # Create Padding variable used for aligning columns
    pad=" "
    while len(pad)<60:
        pad=f"{pad} "
    # Set Column widths
    for row in list:
        for i in range(len(row)):
            if len(row[i])>colsize[i]:
                colsize[i]=len(row[i])
    # Pad each cell with the correct amount of " " characters
    for row in list:
        for i in range(len(row)):
            tmp=row[i]+pad[:colsize[i]]
            row[i]=f"{tmp[:colsize[i]]}"
    # "-" padding for separator lines
    tmp=pad.replace(" ","-")
    # Build Separator line for the top of the table
    out=[dsf.mcb,f"+{tmp[:colsize[0]+2]}+{tmp[:colsize[3]+2]}+{tmp[:colsize[1]+2]}+{tmp[:colsize[2]+2]}+{tmp[:colsize[4]+2]}+"]
    # Build Header Row
    print(list)
    out.append(f'| {list[0][0]} | {list[0][3]} | {list[0][1]} | {list[0][2]} | {list[0][4]} |')
    # Copy Separator Line
    out.append(out[1])
    # Build Table Body
    for row in list[1:]:
        out.append(f'| {row[0]} | {row[3]} | {row[1]} | {row[2]} | {row[4]} |')
    # Bottom Separator
    out.append(out[1])
    out.append(dsf.mcb)
    return out

# MySQL query function
def mysql(query,callerid):
	# Used to toggle Table building
	flag=0
	# Retrive User Perms
	auth=sp.run(["mysql",f'-p{conf.pwd}',f'-h{conf.server}',f'-D{conf.authdb}',f'-eSELECT questperms FROM {conf.authtab} WHERE userid={callerid}'], capture_output=True)
	auth=auth.stdout
	auth=auth.split(b"\n")
	auth=auth[1].decode()
	auth=auth.split(',')
	# Check If All quests Requested
	if query=="-1":
		# Check User Perms
		if '-1' in auth:
			result=sp.run(["mysql",f'-p{conf.pwd}',f'-h{conf.server}',f'-D{conf.questdb}',f'-eSELECT q.questid, q.questname, q.questgiver, c.charname, q.queststatus from quests q join characters c on q.assignedcharid = c.charid'], capture_output=True)
		else:
			flag=1
	else:
		# Sanitize User Input by only allowing terms listed in perms
		req=""
		for i in query.split(','):
			if i in auth or '-1' in auth:
				req+=i+','
		req=req[:-1]
		result=sp.run(["mysql",f'-p{conf.pwd}',f'-h{conf.server}',f'-D{conf.questdb}',f'-eSELECT q.questid, q.questname, q.questgiver, c.charname, q.queststatus from quests q join characters c on q.assignedcharid = c.charid WHERE c.charid in ({req})'], capture_output=True)
	# Process query results
	result=result.stdout
	result=result.split(b"\n")
	for i in range(len(result)):
		result[i]=result[i].split(b"\t")
	for row in result:
		for item in range(len(row)):
			row[item]=row[item].decode()
	# Remove extra item from table
	result.pop()
	if result==[]:
		out=[f"No Visible Quests for ID: {query}"]
	elif flag==0:
		out=convtable(result)
	else:
		out=["You are not authorized to request all quests"]
	return(out)

# Calls when the Bot is linked to the User
@bot.event
async def on_ready():
	global starttime, guilds, channels, roles, features
	print(f"Logged in as {bot.user} (ID: {bot.user.id})")
	starttime=int(time.time())
	print(f"started at: {time.ctime(starttime)} ({starttime})")
	print(f"Owner: {bot.get_user(conf.owner)}")
	# Set empty globals
	guilds=bot.guilds
	for i in guilds:
		channels.append(i.channels)
		roles.append(i.roles)
		features.append(i.features)
	# Unused call to send a message to #general on the first server the bot was joined to
#	await bot.guilds[0].channels[2].send(f"{dsf.bi}{dsf.ul}IT WORKS!!!{dsf.ul}{dsf.bi}")
	print("------")
	# Set bot status when the bot comes up
	await bot.change_presence(activity=discord.Game("With the API"))

# Standard Ping Command
@bot.command()
async def ping(ctx):
	await ctx.send(f"Started At: <t:{starttime}:t> Current Time: <t:{int(time.time())}:t>")

# Kill command (Can only be used by the bot's owner)
@bot.command()
async def kill(ctx):
	# Check permissions
	if ctx.author.id==conf.owner:
		# Kill Bot
		print("user is owner")
		await ctx.send(f"{ctx.author} Is restarting the bot, Please wait")
		await bot.change_presence(activity=discord.Game("REBOOTING"))
		quit()
	else:
		# Report unauthorized Kill attempt
		print(f"{ctx.author} Tried to kill the bot")
		await ctx.send("You are not allowed to do that")

# Command to list quests from MySQL questbook
@bot.command()
async def quests(ctx, query):
	# Query Mysql
	results=mysql(query,ctx.author.id)
	out=""
	# Convert output to single string for passing to discord
	for i in results:
		out+=f"{i}\n"
	# Ensure output is within http post limitations (2000 characters per message)
	if len(out)>1500:
		# If output is too long split output by first row after 1500 characters
		tmp=[]
		for i in range((len(out)//1500)):
			l=out.split('\n')
			l=l[:-2]
			for row in l:
				if tmp==[]:
					# First row of output always makes a new message
					tmp.append(row+'\n')
				elif len(tmp[-1])>1500:
					# Make new message if prior message exceeds 1500 characters
					tmp.append(row+'\n')
				else:
					# If last message in set is not above limit add current row to that message
					tmp[-1]+=(row+'\n')
		await ctx.send(f"{ctx.author}:")
		for i in tmp:
			# Send each row of the message, Removing any preexisting multiline code block tags and putting each message in a multiline code block
			await ctx.send(f"{dsf.mcb}\n{i.lstrip(dsf.mcb).rstrip(dsf.mcb)}{dsf.mcb}")
	else:
		# If message is small enough just send it
		await ctx.send(f"{ctx.author}: \n{out}")

# Run bot with hidden Token
bot.run(conf.token)
