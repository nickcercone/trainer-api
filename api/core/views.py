from ninja import Field, NinjaAPI, Schema
from core.engine import engine
from core.models import Move

api = NinjaAPI()


#class MoveSchema(Schema):
#	start: str = Field(alias='from')
#	end:   str = Field(alias='to')
#	score: float



def serizlaize_move(move):
	return {
		'from': move.start,
		'to': move.end,
		'score': float(move.score)
	}

@api.get('/best')
def get_best(request, line: str = ''):
	line = line.strip()
	move = Move.objects.filter(line=line, type='best').first()
	if move:
		return serizlaize_move(move)
	results = engine(line, depth=20)
	if not results:
		return
	result = results[0]
	move = Move.objects.create(
		line=line,
		start=result['start'],
		end=result['end'],
		score=result['score'],
		type='best'
	)
	return serizlaize_move(move)



def serizlaize_moves(moves):
	return [serizlaize_move(move) for move in moves]

@api.get('/candidates')
def get_candidates(request, line: str = ''):
	line = line.strip()
	moves = Move.objects.filter(line=line, type='candidate')
	if moves:
		return serizlaize_moves(moves)
	results = engine(line, depth=16, lines=10)
	if not results:
		return
	moves = []
	for result in results:
		move = Move.objects.create(
			line=line,
			start=result['start'],
			end=result['end'],
			score=result['score'],
			type='candidate'
		)
		moves.append(move)
	return serizlaize_moves(moves)
