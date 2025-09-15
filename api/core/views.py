from ninja import Field, NinjaAPI, Schema
from core.engine import engine
from core.models import Line, Move, Opening

api = NinjaAPI()


#class MoveSchema(Schema):
#	start: str = Field(alias='from')
#	end:   str = Field(alias='to')
#	score: float





class OpeningSchema(Schema):
	is_white: bool
	slug: str


class OpeningInput(Schema):
	is_white: bool
	slug: str

@api.post('/openings', response=OpeningSchema)
def post_openings(request, data: OpeningInput):
	opening = Opening.objects.filter(slug=data.slug).first()
	if not opening:
		opening = Opening.objects.create(is_white=data.is_white, slug=data.slug)
	return opening


@api.get('/openings', response=list[OpeningSchema])
def get_openings(request):
	return Opening.objects.all()


@api.delete('/openings/{slug}')
def delete_openings(request, slug: str):
	opening = Opening.objects.filter(slug=slug).first()
	if opening:
		opening.delete()







def serizlaize_move(move):
	string = move.line + ' ' + move.start + move.end
	line = Line.objects.filter(line__startswith=string).first()
	return {
		'from': move.start,
		'to': move.end,
		'score': float(move.score),
		'has_line': not not line
	}

@api.get('/best')
def get_best(request, line: str = ''):
	line = line.strip()
	move = Move.objects.filter(line=line, type='best').first()
	if not move:
		results = engine(line, depth=25)
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
	if not moves:
		results = engine(line, depth=18, lines=10)
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





class SaveInput(Schema):
	slug: str
	line: str
	san: str

@api.post('/save')
def post_save(request, data: SaveInput):
	slug = data.slug.strip()
	line = data.line.strip()
	san = data.san.strip()
	# Look for line that is longer than current and return it instead of creating new
	obj = Line.objects.filter(line__startswith=line, slug=slug).first()
	if obj:
		return obj.line
	# Look for line that is shorter than current and extend it
	query = """
		SELECT * FROM core_line
		WHERE (%s LIKE line || '%%') AND slug = %s;
	"""
	obj = Line.objects.raw(query, [line, slug])
	if obj:
		obj = obj[0]
		obj.line = line
		obj.san = san
		obj.save()
		return obj.line
	# Create new record
	obj = Line.objects.create(line=line, san=san, slug=slug)
	return obj.line






class LineSchema(Schema):
	line: str
	san: str

@api.get('/lines', response=list[LineSchema])
def get_lines(request, line: str = '', slug: str = ''):
	line = line.strip()
	lines = Line.objects.filter(line__startswith=line, slug=slug)
	return lines.order_by('line')







@api.get('/valid')
def get_lines(request, line: str = '', slug: str = ''):
	line = line.strip()
	line_parts = line.split(' ')
	prefix = []
	for i in range(len(line_parts)):
		if i % 2 == 0:
			pre = ' '.join(prefix)
			# Look for lines that match prefix
			lines_prefix = Line.objects.filter(line__startswith=pre, slug=slug)
			# Look for lines with prefix + whites next move and compare sizes
			pre_move = ' '.join(prefix + [line_parts[i]])
			lines_prefix_move = Line.objects.filter(line__startswith=pre_move, slug=slug)
			# If they are the same, its valid, if its different its invalid
			if len(lines_prefix) != len(lines_prefix_move):
				return False
		prefix.append(line_parts[i])
	return True






