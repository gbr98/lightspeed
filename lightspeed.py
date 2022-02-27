import numpy as np
import stockfish as sf
import time
from numpy.random import random

import chess
import chess.engine

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import signal
from contextlib import contextmanager


@contextmanager
def timeout(time):
    # Register a function to raise a TimeoutError on the signal.
    signal.signal(signal.SIGALRM, raise_timeout)
    # Schedule the signal to be sent after ``time``.
    signal.alarm(time)

    try:
        yield
    except TimeoutError:
        pass
    finally:
        # Unregister the signal so it won't be triggered
        # if the timeout is not reached.
        signal.signal(signal.SIGALRM, signal.SIG_IGN)


def raise_timeout(signum, frame):
    raise TimeoutError

def FEN(board, white_turn, can_castle, en_passant, count_semi, moves):
	letters = ["0","K","Q","R","B","N","P","p","n","b","r","q","k"]
	castle = ["K","Q","k","q"]
	castle_str = ""
	fen = ""
	for i in range(8):
		empty_count = 0
		for j in range(8):
			if board[i,j] == 0:
				empty_count += 1
			else:
				if empty_count > 0:
					fen += str(empty_count)
					empty_count = 0
				fen += letters[int(board[i,j])]
		if empty_count > 0:
			fen += str(empty_count)
		fen += "/"
	fen = fen[:-1]
	fen += " w " if white_turn else " b "
	for i in range(len(can_castle)):
		castle_str += castle[i] if can_castle[i] else ""
	fen += "-" if len(castle_str) == 0 else castle_str
	fen += " "
	fen += "-" if len(en_passant) == 0 else en_passant
	fen += " "+str(count_semi)+" "
	fen += str(moves)

	return fen

def game(login=True): 

	colors = [".white", ".black"]
	pieces = [".king",".queen",".rook",".bishop",".knight",".pawn"]
	files = ["a","b","c","d","e","f","g","h"]

	driver = webdriver.Firefox()
	logged = False

	while True:

		can_castle = [True, True, True, True] # KQkq
		en_passant = "" # square behind a pawn that just did a 2-square move

		board = np.zeros((8,8))
		last_board = board.copy()

		#stockfish = sf.Stockfish(parameters={"Threads": 1, "Maximum Thinking Time": 1})
		#stockfish = sf.Stockfish("/home/gabriel/Downloads/stockfish_13_linux_x64_bmi2/stockfish_13_linux_x64_bmi2",parameters={"Threads": 1, "Maximum Thinking Time": 10})
		#stockfish.set_elo_rating(2000)
		stockfish = sf.Stockfish()
		stockfish.set_depth(15)

		# sudo apt-get install stockfish
		#engine = chess.engine.SimpleEngine.popen_uci("/usr/games/toga2")

		driver.get("https://lichess.org/")
		WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.CLASS_NAME, "lobby__app__content")))

		if login and not logged:
			logged = True
			driver.find_element_by_class_name("signin").click()
			username = driver.find_element_by_name("username")
			password = driver.find_element_by_name("password")
			username.send_keys("gbr98razr")
			password.send_keys("141568313tijolos")
			#username.send_keys("gbr98")
			#password.send_keys("141568313")
			driver.find_element_by_class_name("submit").click()
			WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.CLASS_NAME, "lobby__app__content")))

		time.sleep(2)
		driver.find_element_by_css_selector("[data-id='3+0']").click()
		WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.CLASS_NAME, "main-board")))
		time.sleep(2)

		def elm_pos(elm):
			return np.array(str(elm.value_of_css_property("transform")).replace(")","").split(",")[-2:]).astype(np.float)

		def get_pos_by_class(driver, classname):
			pos = []
			sample_elm = driver.find_elements_by_css_selector(classname)
			for elm in sample_elm:
				pos.append(elm_pos(elm))
			return pos

		zero_pos = get_pos_by_class(driver,".rook")[-1]
		sample_pos = get_pos_by_class(driver,".knight")[-1]
		unit = np.abs((sample_pos - zero_pos)[0])
		print(unit,"pixels per unit")

		playing_white = get_pos_by_class(driver,".white.king")[0][1] > 3*unit
		print("playing white?", playing_white)

		def check_play(driver):
			return len(driver.find_elements_by_css_selector(".rclock-bottom.running")) > 0

		def check_end(driver):
			return len(driver.find_elements_by_css_selector(".follow-up")) > 0

		def read_board(colors, pieces, driver, unit):
			board = np.zeros((8,8))
			for i in range(len(colors)):
				for j in range(len(pieces)):
					pos = get_pos_by_class(driver, colors[i]+pieces[j])
					for position in pos:
						rank = round(position[0]/unit)#????
						file = round(position[1]/unit)
						board[rank,file] = (-2*i+1)*(j+1)
						#print(colors[i],pieces[j],position)
			return board.T

		def flip_board(board):
			new_board = []
			for i in range(8):
				new_board.append(board[7-i])
			return np.flip(np.array(new_board), 1)

		fen = ""
		semi_moves = 0
		moves = 1

		if not playing_white:
			#last_board = read_board(colors, pieces, driver, unit)
			#last_board = flip_board(last_board)
			last_board = np.array([[-3,-5,-4,-2,-1,-4,-5,-3],
								  [-6,-6,-6,-6,-6,-6,-6,-6],
								  [ 0, 0, 0, 0, 0, 0, 0, 0],
								  [ 0, 0, 0, 0, 0, 0, 0, 0],
								  [ 0, 0, 0, 0, 0, 0, 0, 0],
								  [ 0, 0, 0, 0, 0, 0, 0, 0],
								  [ 6, 6, 6, 6, 6, 6, 6, 6],
								  [ 3, 5, 4, 2, 1, 4, 5, 3]])
			fen = FEN(board, True, can_castle, en_passant, semi_moves, moves)
			print(fen)
			semi_moves += 1

		adapt = False
		finished = False
		while not finished:

			if check_end(driver):
				print("game ended")
				break
			
			if not check_play(driver) and moves > 1:
				continue

			try:
				board = read_board(colors, pieces, driver, unit)
			except:
				time.sleep(0.2)
				continue
			if not playing_white:
				board = flip_board(board)
			'''
			time.sleep(0.5)
			board_check = read_board(colors, pieces, driver, unit)
			if not playing_white:
				board_check = flip_board(board_check)
			'''
			if moves < 2:
				if (board == last_board).all() or adapt:
					adapt = False
					continue
			
			# update can castle
			if board[7, 4] != 1:
				can_castle[0] = False
				can_castle[1] = False
			if board[0, 4] != -1:
				can_castle[2] = False
				can_castle[3] = False
			if board[7,7] != 3:
				can_castle[0] = False
			if board[7,0] != 3:
				can_castle[1] = False
			if board[0,7] != -3:
				can_castle[2] = False
			if board[0,0] != -3:
				can_castle[3] = False

			# en passant?
			diff = board - last_board
			ip, jp = np.where(diff == 6)
			im, jm = np.where(diff == -6)
			if len(ip) == 1 and len(im) == 1 and jp[0] == jm[0] and np.abs(im[0]-ip[0]) == 2:
				en_passant = files[jp[0]] + str(int(ip[0]+(1 if playing_white else -1)+1))
			else:
				en_passant = ""

			fen = FEN(board, playing_white, can_castle, en_passant, semi_moves, moves)

			print(board)
			print(fen)
			
			try:
				stockfish.set_fen_position(fen)
			except:
				print("incorrect FEN")
				time.sleep(0.2)
				continue
			#move = stockfish.get_best_move()
			'''
			try:
				with timeout(2):
					move = stockfish.get_best_move_time(time_think)
			except TimeoutError:
				print("retrying with 10ms")
				move = stockfish.get_best_move_time(10)
			'''
			done = False
			while not done:
				try:
					time_think = int(random()*100 + 50)
					print("thinking for",time_think,"ms")
					engine = chess.engine.SimpleEngine.popen_uci("/usr/games/stockfish")
					board_chess = chess.Board(fen)
					result = engine.play(board_chess, chess.engine.Limit(time=time_think/1000.0))
					engine.quit()
					#print(result)
					print(result.move)
					move = str(result.move)
					done = True
				except:
					move = str(list(board_chess.legal_moves)[int(random()*board_chess.legal_moves.count())])
					done = True
					#engine.quit()
					print("retrying...")

			# bot move
			#time.sleep(random()*8)
			start_i = 8-int(move[1]) if playing_white else int(move[1])-1
			start_j = int(files.index(move[0])) if playing_white else 7-int(files.index(move[0]))
			end_i = 8-int(move[3]) if playing_white else int(move[3])-1
			end_j = int(files.index(move[2])) if playing_white else 7-int(files.index(move[2]))
			el = driver.find_element_by_class_name("main-board")
			action = webdriver.common.action_chains.ActionChains(driver)
			action.move_to_element_with_offset(el, start_j*unit + unit/2, start_i*unit + unit/2)
			action.click()
			action.move_to_element_with_offset(el, end_j*unit + unit/2, end_i*unit + unit/2)
			action.click()
			'''
			if (end_i == 0 and board[start_i, start_j] == 6) or (end_i == 7 and board[start_i, start_j] == -6):
				action.move_to_element_with_offset(el, end_j*unit + unit/2, end_i*unit + unit/2)
				action.click()
				action.click()
			'''
			action.perform()
			#time.sleep(0.5)

			#input("make the move")
			#move = stockfish.get_best_move_time(1000)

			'''
			last_board = board.copy()

			if len(move) == 4:
				start_i = 8-int(move[1])
				start_j = int(files.index(move[0]))
				end_i = 8-int(move[3])
				end_j = int(files.index(move[2]))
				board[end_i, end_j] = board[start_i, start_j]
				board[start_i, start_j] = 0
				if np.abs(board[end_i, end_j]) == 6 and last_board[end_i, end_j] == 0 and np.abs(start_j-end_j) == 1: #en passant
					board[start_i+(-1 if playing_white else 1), start_j] = 0
				if np.abs(board[end_i, end_j]) == 1 and end_j - start_j == 2: #kingside castle
					board[end_i, 5] = board[end_i, 7]
					board[end_i, 7] = 0
				if np.abs(board[end_i, end_j]) == 1 and end_j - start_j == -2:#queenside castle
					board[end_i, 3] = board[end_i, 0]
					board[end_i, 0] = 0
			
			print(board)
			adapt = True
			'''
			last_board = board.copy()
			semi_moves += 2
			moves += 1



if __name__ == "__main__":
	game(True)