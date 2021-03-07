import json
from user import *



def haveActiveWager(user, wagers):
	for wager in wagers.keys():
		return wager == user
	return False


def canBet(better, amount, users):
    return int(amount) <= int(users[better].points)



async def createAllUserStats(guild):
	users = {}
	for member in guild.members:
		userId = await guild.fetch_member(member.id)
		users[member.id] = User(userId, 1000, 0, 0)

	f = open("stats.txt" , "w")
	for user in users.values():
		f.write(str(user.id) + " " + str(user.points) + " " + str(user.win) + " " + str(user.loss) + "\n")
	f.close()

	return users

def updateUserDataWithNew(users):
    f = open("stats.txt" , "w")
    for user in users.values():
    	f.write(str(user.id) + " " + str(user.points) + " " + str(user.win) + " " + str(user.loss) + "\n")
    f.close()
