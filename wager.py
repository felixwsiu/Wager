class Wager:
	def __init__(self, user, desc, opt1, opt2):
		self.user = user
		self.desc = desc
		self.opt1 = opt1
		self.opt2 = opt2
		self.opt1bets = []
		self.opt2bets = []
		self.betters = []
		self.pot = 0
		self.open = True
		self.aWeight = 0
		self.bWeight = 0
		self.aOdds = 0
		self.bOdds = 0

