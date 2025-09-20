from os import stat
import time
from ninja import NinjaAPI, Schema
from core.engine import engine
from core.models import Line, Opening, Position
from django.db.models.functions import Length


api = NinjaAPI()






#---------------
#	Openings
#---------------



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
	Opening.objects.filter(slug=slug).delete()
	Line.objects.filter(slug=slug).delete()














#----------------------
#	Moves/Positions
#----------------------



class MoveSchema(Schema):
	score: float
	move: str
	has_line: bool

	@staticmethod
	def resolve_move(obj):
		parts = [item for item in obj.line.split(' ') if item]
		return parts[-1]

	@staticmethod
	def resolve_has_line(obj, context):
		slug = context.get('slug')
		line = Line.objects.filter(slug=slug, line__startswith=obj.line).first()
		print('context', context, obj)
		#return False
		return not not line

class MovesSchema(Schema):
	active: bool
	next: str
	options: list[MoveSchema]



@api.get('/moves',
	#response=MovesSchema
)
def get_moves(request, line: str = '', slug: str = ''):
	line = line.strip()
	slug = slug.strip()
	
	t = time.time()

	# Fixture out if next move is for white or black
	line_parts = [item for item in line.split(' ') if item]
	is_white = len(line_parts) % 2 == 0

	# Is the move for the active player
	active = False
	opening = Opening.objects.filter(slug=slug).first()
	if opening:
		if opening.is_white and is_white:
			active = True
		if not opening.is_white and not is_white:
			active = True

	# Load options
	if not line:
		options = Position.objects.annotate(length=Length('line')).filter(
			length=4
		)
	else:
		options = Position.objects.annotate(length=Length('line')).filter(
			line__startswith=line,
			length=len(line) + 5
		)
	
	# Generate positions/scores if not found
	if not options:
		options = []
		results = engine(line, lines=3)
		for result in results:
			l = result.get('line')
			position = Position.objects.filter(line=l).first()
			if not position:
				position = Position.objects.create(
					score=result.get('score'),
					line=l,
				)
			options.append(position)
	
	# Sort options by score
	options = sorted(options, key=lambda move: move.score)
	if is_white:
		options.reverse()

	print(f'Duration: {time.time() - t:.1f}')

	
	# Get active players next move
	next = ''
	if active:
		next_line = Line.objects.annotate(length=Length('line')).filter(
			slug=slug,
			line__startswith=line,
			length__gt=len(line)
		).first()
		if next_line:
			l = next_line.line[len(line):]
			l = l.strip()
			l = l.split(' ')
			next = l[0]


	data = MovesSchema.model_validate({
		'active': active,
		'next': next,
		'options': options
	}, context={'slug': slug})

	# Return packet
	return data



@api.get('/eval',
)
def get_eval(request, line: str = ''):
	line = line.strip()
	
	# Look for position
	position = Position.objects.filter(line=line).first()
	if position:
		return float(position.score)

	# Generate missing position
	results = engine(line, lines=1)
	if results:
		result = results[0]
		position = Position.objects.create(
			score=result.get('score'),
			line=line,
		)
		return float(position.score)

	return 0
















#------------
#	Lines
#------------



class LineSchema(Schema):
	id: int
	line: str
	san: str

@api.get('/lines', response=list[LineSchema])
def get_lines(request, line: str = '', slug: str = ''):
	line = line.strip()
	lines = Line.objects.filter(line__startswith=line, slug=slug)
	return lines.order_by('line')



class LineInput(Schema):
	slug: str
	line: str
	san: str

@api.post('/lines')
def post_lines(request, data:LineInput):
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



@api.delete('/lines/{id}')
def delete_lines(request, id: int):
	line = Line.objects.filter(id=id).first()
	if line:
		line.delete()










