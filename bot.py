import os
import discord
import json

from tokens import DISCORD_TOKEN
from discord.ext import commands
from wager import *
from bet import *
from userUtil import *
from user import *

intents = discord.Intents.all()

#client = Discord.client()
bot = commands.Bot(command_prefix="$", intents=intents)



global users
global wagers
users = {}
wagers = {}

#Load in user stats from the server, create a new file if it does not exist


@bot.event
async def on_ready():
    global users
    with open("stats.txt") as f:
        userStats = f.readlines()
        if userStats:
            for user in userStats:
                userData = user.split()
                users[userData[0]] = User(userData[0], float(userData[1]), int(userData[2]), int(userData[3]))
        else:
            guild = discord.utils.get(bot.guilds, name="thou")
            users = await createAllUserStats(bot.guilds[0])





@bot.command(name="start", help="Initiates a Wager   $start {desc} {opt1} {opt2}", pass_context=True)
async def start_wager(ctx, desc, opt1, opt2):
    global wagers
    authortag = ctx.message.author.name + "#" + ctx.message.author.discriminator


    if haveActiveWager(authortag, wagers):
        response = ctx.message.author.mention + " already has an active wager. Users may only have one active at a time."
    else:
        wagers[authortag] = Wager(ctx.message.author, desc, opt1, opt2)

        response = """{user} has begun a Wager!
        Description: {desc}
        A: {opt1}
        B: {opt2}
        """.format(user=ctx.message.author.mention , desc=desc, opt1=opt1, opt2=opt2)

    await ctx.send(response)


@bot.command(name="bet", help="Bet on an active Wager   $bet {userId of host} {amount} {A or B}", pass_context=True)
async def bet(ctx, user, amount, opt):
    global users
    global wagers
    wager = None
    authortag = ctx.message.author.name + "#" + ctx.message.author.discriminator

    if wagers:
        wager = wagers.get(user)


    if not wagers:
        response = ctx.message.author.mention + " No wager is active at this time."
    elif wager.open == False:
        response = ctx.message.author.mention + " The wager has already been locked in! You cannot bet at this time."
    elif not (opt == "A" or opt == "B"):
        response = ctx.message.author.mention + " That is not a valid option, choose A or B."
    elif user not in wagers.keys():
        response = user + " does not have an active wager."
    elif not canBet(authortag, amount, users):
        response = ctx.message.author.mention + " is too broke to bet LOL."
    elif authortag in wager.betters:
        response = ctx.message.author.mention + " You have already bet on this wager. Good luck!"
    else:
        bet = Bet(authortag, amount)
        optiondesc = ""

        if opt == "A":
            wager.opt1bets.append(bet)
            optiondesc = wager.opt1
        else:
            wager.opt2bets.append(bet)
            optiondesc = wager.opt2
        wager.pot += int(amount)
        wager.betters.append(authortag)

        currUser = users[authortag]
        users[authortag] = User(currUser.id, int(currUser.points) - int(amount), currUser.win, currUser.loss)
        updateUserDataWithNew(users)
        response = ctx.message.author.mention + " has made a " + amount + " bet on '" + optiondesc + "' for " + user + "'s Wager!"


    await ctx.send(response)


@bot.command(name="lock", help="Lock in your active wager and prevent new bets   $lock", pass_context=True)
async def lock(ctx):
    global users
    global wagers
    authortag = ctx.message.author.name + "#" + ctx.message.author.discriminator
    wager = wagers.get(authortag)

    if not haveActiveWager(authortag, wagers):
        response = ctx.message.author.mention + " You do not have an active wager to lock in."
    elif wager.open == False:
        response = ctx.message.author.mention + " Your wager is already locked in."
    elif not wager.opt1bets or not wager.opt2bets:
        response = ctx.message.author.mention + " Atleast 1 bet must be made on each option."
    else:
        betters1 = betters2 = ""
        aTotal = bTotal = 0.0
        aOdds = bOdds = 0.0
        aWeight = bWeight = 0

        for bet in wager.opt1bets:
            betters1 += bet.user + " "
            aTotal += int(bet.amount)

        for bet in wager.opt2bets:
            betters2 += bet.user + " "
            bTotal += int(bet.amount)

        aOdds = bTotal / aTotal
        bOdds = aTotal / bTotal
        aWeight = round(aTotal / wager.pot,2)
        bWeight = round(bTotal / wager.pot,2)

        wager.open = False
        wager.aOdds = aOdds
        wager.bOdds = bOdds
        wager.aWeight = aWeight
        wager.bWeight = bWeight

        wagers[authortag] = wager
        response = """
        {user}'s wager has locked in! No more bets 8)
        Total Pot: {pot}
        Betters on {opt1} : {betters1}
        Betters on {opt2} : {betters2}
        A Odds: {aOdds} for 1
        B Odds: {bOdds} for 1
        Distribution:  {aWeight} - {bWeight}
        """.format(user=ctx.message.author.mention , pot=wager.pot, opt1=wager.opt1, opt2=wager.opt2, betters1=betters1, betters2=betters2
                    ,aOdds = aOdds, bOdds = bOdds, aWeight = aWeight, bWeight = bWeight)

    await ctx.send(response)

@bot.command(name="end", help="End the wager and distribute points   $end {A or B - the winning side}", pass_context=True)
async def end(ctx, opt):
    global users
    global wagers
    authortag = ctx.message.author.name + "#" + ctx.message.author.discriminator
    wager = wagers.get(authortag)
    if not haveActiveWager(authortag, wagers):
        response = ctx.message.author.mention + " You do not have an active wager."
    elif wager.open == True:
        response = ctx.message.author.mention + " Your wager must be locked in before it can end."
    elif not ( opt == "A" or opt == "B" ):
        response = ctx.message.author.mention + " Choose A or B to indicate the winning side."
    else:
        winners = []
        losers = []
        if opt == "A":
            for bet in wager.opt1bets:
                gain = int(bet.amount) + int(bet.amount) * wager.aWeight
                user = users[bet.user]
                users[bet.user] = User(user.id, user.points + gain, user.win + 1, user.loss)
                winners.append( (user.id, "+ " + str(gain) ))

            for bet in wager.opt2bets:
                user = users[bet.user]
                users[bet.user] = User(user.id, user.points, user.win, user.loss + 1)
                losers.append( (user.id, "- " + str(bet.amount) ))
        else:
            for bet in wager.opt1bets:
                user = users[bet.user]
                users[bet.user] = User(user.id, user.points, user.win, user.loss + 1)
                losers.append( (user.id, "- " + str(bet.amount) ))

            for bet in wager.opt2bets:
                gain = int(bet.amount) + int(bet.amount) * wager.bWeight
                user = users[bet.user]
                users[bet.user] = User(user.id, user.points + gain, user.win + 1, user.loss)
                winners.append( (user.id, "+ " + str(gain) ))

        updateUserDataWithNew(users)
        wagers.pop(authortag)
        response = """
                {user}'s wager has ended with '{opt}' winning!
                Description: {desc}
                A: {opt1}
                B: {opt2}

                Total Pot: {pot}
                Winners : {winners}
                Losers : {losers}
                """.format(user=ctx.message.author.mention , opt=opt, desc=wager.desc, opt1=wager.opt1, opt2=wager.opt2,
                        pot=wager.pot, winners=winners, losers=losers)
    await ctx.send(response)

@bot.command(name="status", help="Check the status on an active wager   $status {userId}", pass_context=True)
async def status(ctx, user):
    if not haveActiveWager(user, wagers):
        response = user + " does not have an active wager."
    else:
        wager = wagers.get(user)
        response = """
                Status on {user}'s active wager
                Description: {desc}
                A: {opt1}
                B: {opt2}
                Total Pot: {pot}
                All Betters: {betters}
                Locked in? : {open}
                A Odds: {aOdds} for 1
                B Odds: {bOdds} for 1
                Distribution:  {aWeight} - {bWeight}
                """.format(user=user , desc=wager.desc, opt1=wager.opt1, opt2=wager.opt2, pot=wager.pot, betters=wager.betters, open=not wager.open
                        , aOdds = wager.aOdds, bOdds = wager.bOdds, aWeight = wager.aWeight, bWeight = wager.bWeight)

    await ctx.send(response)


@bot.command(name="points", help="Check how many points you have   $points", pass_context=True)
async def points(ctx):
    global users
    authortag = ctx.message.author.name + "#" + ctx.message.author.discriminator
    response = "You have : " + str(int(users[authortag].points)) + " points!"
    await ctx.send(response)

#@bot.event
#async def on_command_error(ctx, error):
#   await ctx.send('Invalid command, $help for more information')

bot.run(DISCORD_TOKEN)