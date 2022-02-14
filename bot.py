#!/usr/bin/python3
import discord
from discord.ext import commands
import discordauth as dauth
import sqlauth as sauth
import time
import botsettings
import subprocess as sp
import dsformat as dsf
intents=discord.Intents.default()
intents.members=True
bot=commands.Bot(command_prefix=botsettings.prefix,owner_id=botsettings.owner,intents=intents)
activities=["Awaiting Input","Processing","Querying Database","Error"]
activity=0
starttime=0
guilds=[]
channels=[]
roles=[]
features=[]
# END VARIABLE DEFINITIONS

def convtable(list):
    colsize=[0,0,0,0,0]
    pad=" "
    while len(pad)<60:
        pad=f"{pad} "
    for row in list:
        for i in range(len(row)):
            if len(row[i])>colsize[i]:
                colsize[i]=len(row[i])
    for row in list:
        for i in range(len(row)):
            tmp=row[i]+pad+pad
            row[i]=f"{tmp[:colsize[i]]}"
    tmp=pad.replace(" ","-")+pad.replace(" ","-")
    out=[dsf.mcb,f"+{tmp[:colsize[0]+2]}+{tmp[:colsize[3]+2]}+{tmp[:colsize[1]+2]}+{tmp[:colsize[2]+2]}+{tmp[:colsize[4]+2]}+"]
    out.append(f'| {list[0][0]} | {list[0][3]} | {list[0][1]} | {list[0][2]} | {list[0][4]} |')
    out.append(out[1])
    for row in list[1:]:
        out.append(f'| {row[0]} | {row[3]} | {row[1]} | {row[2]} | {row[4]} |')
    out.append(out[1])
    out.append(dsf.mcb)
    return out

def mysql(query,callerid):
	flag=0
	auth=sp.run(["mysql",f'-p{sauth.pwd}',f'-h{sauth.server}','-Dbots',f'-eSELECT questperms FROM dndperms WHERE userid={callerid}'], capture_output=True)
	auth=auth.stdout
	auth=auth.split(b"\n")
	auth=auth[1].decode()
	auth=auth.split(',')
	if query=="-1":
		if '-1' in auth:
			result=sp.run(["mysql",f'-p{sauth.pwd}',f'-h{sauth.server}','-DDnD',f'-eSELECT q.questid, q.questname, q.questgiver, c.charname, q.queststatus from quests q join characters c on q.assignedcharid = c.charid'], capture_output=True)
		else:
			return("You are not authorized to request all quests")
			flag=1
	else:
		req=""
		for i in query.split(','):
			if i in auth or '-1' in auth:
				req+=i+','
		req=req[:-1]
		result=sp.run(["mysql",f'-p{sauth.pwd}',f'-h{sauth.server}','-DDnD',f'-eSELECT q.questid, q.questname, q.questgiver, c.charname, q.queststatus from quests q join characters c on q.assignedcharid = c.charid WHERE c.charid in ({req})'], capture_output=True)
	result=result.stdout
	result=result.split(b"\n")
	for i in range(len(result)):
		result[i]=result[i].split(b"\t")
	for row in result:
		for item in range(len(row)):
			row[item]=row[item].decode()
	result.pop()
	if flag==0:
		out=convtable(result)
	else:
		out=[result]
	return(out)

@bot.event
async def on_ready():
	global starttime, guilds, channels, roles, features
	print(f"Logged in as {bot.user} (ID: {bot.user.id})")
	starttime=int(time.time())
	print(f"started at: {time.ctime(starttime)} ({starttime})")
	print(f"Owner: {bot.get_user(botsettings.owner)}")
	guilds=bot.guilds
	for i in guilds:
		channels.append(i.channels)
		roles.append(i.roles)
		features.append(i.features)
#	await bot.guilds[0].channels[2].send(f"{dsf.bi}{dsf.ul}IT WORKS!!!{dsf.ul}{dsf.bi}")
	print("------")
	await bot.change_presence(activity=discord.Game("With the API"))

@bot.command()
async def ping(ctx):
	await ctx.send(f"Started At: <t:{starttime}:t> Current Time: <t:{int(time.time())}:t>")

@bot.command()
async def kill(ctx):
	if ctx.author.id==botsettings.owner:
		print("user is owner")
		await ctx.send(f"{ctx.author} Is restarting the bot, Please wait")
		await bot.change_presence(activity=discord.Game("REBOOTING"))
		quit()
	else:
		print(f"{ctx.author} Tried to kill the bot")
		await ctx.send("You are not allowed to do that")

@bot.command()
async def quests(ctx, query):
	results=mysql(query,ctx.author.id)
	out=""
	for i in results:
		out+=f"{i}\n"
	if len(out)>1500:
		tmp=[]
		for i in range((len(out)//1500)+1):
			tmp.append(out[i*1500:(i+1)*1500])
		await ctx.send(f"{ctx.author}:")
		for i in tmp:
			await ctx.send(f"{dsf.mcb}\n{i.lstrip(dsf.mcb).rstrip(dsf.mcb)}{dsf.mcb}")
	else:
		await ctx.send(f"{ctx.author}: \n{out}")

# Run bot with hidden Token
bot.run(dauth.token)
