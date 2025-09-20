import subprocess
import time

# Path to Stockfish binary (adjust if needed)
STOCKFISH_PATH = "/home/nick/Downloads/stockfish-ubuntu-x86-64-avx2/stockfish/stockfish-ubuntu-x86-64-avx2"



def engine(moves, move=None, depth=25, lines=1):

	moves_parts = [item for item in moves.split(' ') if item]
	is_white = len(moves_parts) % 2 == 0
	#print('Parts', moves_parts)
	#if is_white:
	#	print('Whites move!')
	#else:
	#	print('Blacks move!')
	#print('Depth:', depth)
	#print('Lines:', lines)
	# Start Stockfish process
	process = subprocess.Popen(
		STOCKFISH_PATH,
		stdin=subprocess.PIPE,
		stdout=subprocess.PIPE,
		text=True,
		bufsize=1
	)
	# UCI commands for Stockfish
	commands = [
		'uci',               # Initialize UCI mode
		'isready',           # Check if engine is ready
		f'position startpos moves {moves}', # Set starting position
		f'setoption name MultiPV value {lines}', # How many lines
		f'setoption name Threads value 1', # How many lines
		f'go depth {depth} searchmoves {move}' if move else f'go depth {depth}'        # Search to depth 15
	]
	# Send commands and collect output
	for cmd in commands:
		process.stdin.write(cmd + "\n")
		process.stdin.flush()
	
	# Wait for Stockfish to process (adjust sleep for deeper searches)
	time.sleep(0.5)
	
	# Read output until we get the final response
	messages = []
	while True:
		line = process.stdout.readline().strip()
		if line:
			messages.append(line)
		if 'bestmove' in line:  # Stop when bestmove is received
			break

	# Terminate the process
	process.stdin.close()
	process.terminate()
	process.wait()

	# Get list of moves with evaluation of strength
	results = []
	for line in messages:
		if line.startswith(f'info depth {depth}'):
			parts = line.split()
			if 'cp' not in parts or 'pv' not in parts:
				continue
			score = int(parts[parts.index('cp') + 1]) / 100.0
			if not is_white:
				score = -score
			move = parts[parts.index('pv') + 1]
			results.append({
				'score': score,
				'move': move,
				'line': ' '.join([moves, move]).strip()
			})

	# What if i dont get what i expect
	if len(results) != lines:
		print('Move len not equal to lines :(')
		for line in messages:
			print(line)
	
	return results





if __name__ == '__main__':
	t = time.time()
	# Run commands and get output
	moves = engine('e2e4', lines=3)
	for line in moves:
		print(line)
		#eval = engine('', move='a2a4')
		#	print(eval)

	print(time.time() - t)

