#!/usr/bin/env python
import math
import time
import csv
import cli.app

def get_days():
	'''Returns time in days since epoch.'''

	days = time.time()/float(60*60*24)
	return days

def compute_score(prompt_tuple):
	'''This method takes a (prompt, time, count_correct, ebb_score) tuple. 
	It returns the Ebbinghaus Score (a float)'''

	time_now = get_days()

	prompt = prompt_tuple[0] #string
	elapsed_time = time_now - float(prompt_tuple[1]) #seconds --float
	count_correct = float(prompt_tuple[2]) # int

	ebb_score = math.exp(-(elapsed_time/count_correct))
	return ebb_score
	
def pick_question(prompt_list):
	'''This method takes a list of (prompt, time, count_correct, ebb_score) tuples
	that is sorted (ascending) by the ebbinghaus retention score, ebb_score.
	It pops the top one off, with the lowest ebbinghaus score.'''
	return prompt_list.pop()
	
def sort_question_list(prompt_list):	
	'''This method takes a list of (prompt, time, count_correct, ebb_score) tuples, 
	where prompt, time, count_correct are updated, and computes new ebb_scores.
	It returns the sorted list (ascending) by the new ebbinghaus retention score.
	'''
	sorted_question_list = []
	for prompt_tuple in prompt_list:
		prompt = prompt_tuple[0] #string
		time = float(prompt_tuple[1]) #seconds --float
		count_correct = int(prompt_tuple[2]) # int

		new_ebb_score = compute_score(prompt_tuple)
		sorted_question_list.append(
			(prompt, time, count_correct, new_ebb_score)
		)

	slist = sorted(sorted_question_list, key=lambda tpl: tpl[3], reverse=True) #sort by ebbinghaus score
	return slist

def grade_question(prompt_tuple, answer_sheet):
	'''This method grades a prompt tuple, updates its time and count_correct
	and then returns the updated tuple. It needs an answer sheet.'''

	prompt = prompt_tuple[0] #string
	last_time = float(prompt_tuple[1]) #days --float
	count_correct = int(prompt_tuple[2]) # int
	ebb_score = float(prompt_tuple[3])

	print prompt #print the prompt to the question
	raw_input("Press any key to get the correct answer")
	print lookup_answer(prompt, answer_sheet)
	correct = raw_input("Did you get it correct? Y/n" )
	if correct in set(["Y", "y"]):
		count_correct += 1
	
	# Return the prompt_tuple, with count_correct, and the time updated
	return (prompt, get_days(), count_correct, ebb_score) #note that ebb_score is NOT updated

def lookup_answer(prompt, answer_sheet):
	# answer_sheet is a hash
	try:
		return answer_sheet[prompt]	
	except KeyError:
		print "The answer sheet does not have the necessary prompt"
		print "Make sure the answer sheet matches the grade_sheet's prompts"
		exit(1)

def load_answer_sheet(answer_sheet_csv):
	'''this method takes a file, answer_sheet_csv, and returns its info in a hash'''
	answer_sheet = {}
	reader = csv.reader(open(answer_sheet_csv))
	for row in reader:
		if answer_sheet.has_key(row[0]):
			pass
		else:
			answer_sheet[row[0]] = row[1]
	return answer_sheet

def load_grade_sheet(answer_sheet_hash, grade_sheet_csv=None):
	'''this method takes a hash, answer_sheet, and maybe a grade_sheet_csv
	If there is no grade_sheet_csv, it makes one out of the answer sheet with very 
	low ebbinghaus scores. Else, it loads it up'''
	time_now = get_days()
	grade_sheet = []
	if grade_sheet_csv is None:
		for prompt in answer_sheet_hash.keys():
			grade_sheet.append((prompt, time_now, 1, 0.0))
	else:
		grade_file = open(grade_sheet_csv)
		reader = csv.reader(grade_file)
		for row in reader:
			grade_sheet.append((row[0], row[1], row[2], row[3]))
		grade_file.close()
	return grade_sheet

def write_grade_sheet(prompt_list, topic_name):
	'''This method takes the prompt list in memory and writes it out to a csv file
	for future use: "./topic_name.csv" 

	Use this method at the end of a session, to keep track of things.
	'''
	sorted_prompt_list = sorted(prompt_list, key=lambda tpl: tpl[3]) #sort by ebbinghaus score
	#prompt_writer = csv.writer(open("./%s.csv" % topic_name, "wb"))
	prompt_writer = csv.writer(open(topic_name, "wb"))
	for prompt_tuple in prompt_list:
		prompt_writer.writerow(list(prompt_tuple))

@cli.app.CommandLineApp
def spaced_repetition(app):
	if app.params.answer_sheet is not None:
		answer_sheet_hash = load_answer_sheet(app.params.answer_sheet)
	else:
		print "You need to provide an answer sheet csv"
		exit(1)

	prompt_list = load_grade_sheet(answer_sheet_hash, app.params.grade_sheet)
	print "Starting app"
	keep_going = raw_input("Do a question? Y/n: ")
	while keep_going == "Y":
		question_tuple = pick_question(prompt_list)
		graded_question = grade_question(question_tuple, answer_sheet_hash)
		prompt_list.append(tuple([str(elt) for elt in graded_question]))
		prompt_list = sort_question_list(prompt_list)
		keep_going = raw_input("Do a question? Y/n: ")
	else:
		print "Exiting"
		if app.params.grade_sheet is None:
			write_grade_sheet(prompt_list, "".join(["grades_of_", app.params.answer_sheet]))
		else:
			write_grade_sheet(prompt_list, app.params.grade_sheet) 
		
spaced_repetition.add_param("-g", "--grade-sheet", help="grade sheet to load", default=None, dest="grade_sheet")
spaced_repetition.add_param("-a", "--answer-sheet", help="list in long format", default=None, dest="answer_sheet")

if __name__ == "__main__":
    spaced_repetition.run()

