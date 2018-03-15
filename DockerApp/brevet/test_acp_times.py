"""
Nose tests for acp_times.py

Implemented by: Andrew Werderman
"""
import nose 
from acp_times import open_time, close_time
import arrow

'''
The calculator converts all inputs expressed in units of miles to kilometers 
and rounds the result to the nearest kilometer before being used in 
calculations. Times are rounded to the nearest minute.

Most tests from examples at https://rusa.org/octime_alg.html
'''

START_TIME = arrow.now()
BREVET_DISTANCES = [200, 300, 400, 600, 1000]

###
# open_time tests
#	Specifically testing the open_time function with 
#	differnt values.
# 
# open_time(control_dist_km, brevet_dist_km, brevet_start_time)
###

def test_start_point_open():
	''' Should return: official start time '''
	assert open_time(0, BREVET_DISTANCES[0], START_TIME) == START_TIME


def test_first_interval_open():
	''' 
	Max speed for control 0 <= dist <= 200 is 34 km/hr
	Control at 175 --> 5H09 = 309 mins
	'''
	assert open_time(175, BREVET_DISTANCES[0], START_TIME) == START_TIME.shift(minutes=309)


def test_second_interval_open_1():
	'''
	Max speed for control 200 < dist <= 400 is 32 km/hr
	Control at 250 --> 7H27 = 5H53 + 1H34 = 353 + 94 = 447 mins
	'''
	assert open_time(250, BREVET_DISTANCES[1], START_TIME) == START_TIME.shift(minutes=447)


def test_second_interval_open_2():
	'''
	Max speed for control 200 < dist <= 400 is 32 km/hr
	Control at 350 --> 10H34 = 5H53 + 4H41 = 353 + 281 = 634 mins
	'''
	assert open_time(350, BREVET_DISTANCES[2], START_TIME) == START_TIME.shift(minutes=634)


def test_third_interval_open():
	'''
	Max speed for control 400 < dist <= 600 is 30 km/hr
	Control at 550 --> 17H08 = 1028 mins
	'''
	assert open_time(550, BREVET_DISTANCES[3], START_TIME) == START_TIME.shift(minutes=1028)


def test_fourth_interval_open():
	'''
	Max speed for control dist > 600 is 28 km/hr (maximum brevet is 1000km)
	Control at 890 --> 29H09 = 1749 mins
	'''
	assert open_time(890, BREVET_DISTANCES[4], START_TIME) == START_TIME.shift(minutes=1749)


def test_equal_to_finish_point_open():
	''' 
	Should be calculated the same way 
	Control at 1000 = 890km + 110km --> 29H09 + 3H56 = 1749 + 236 = 
	'''
	assert open_time(1000, BREVET_DISTANCES[4], START_TIME) == START_TIME.shift(minutes=1985)


def test_longer_than_finish_point_open():
	''' 
	Open times for finishing checkpoints are calculated by theoretical
	distance instead of actual. i.e. 209km uses 200km to calculate opening time
	'''
	assert open_time(1009, BREVET_DISTANCES[4], START_TIME) == START_TIME.shift(minutes=1985)


def test_decimal_distance_1():
	''' distances should be rounded to nearest km '''
	assert open_time(175.3, BREVET_DISTANCES[0], START_TIME) == START_TIME.shift(minutes=309)


def test_decimal_distance_2():
	''' 
	distances should be rounded to nearest km 
	
	This test found some weird behavior by the built-in round function for python.
	round(174.5) rounds to 174 probably because of the floating point rep.

	FIX PYTHON ROUND FUNCTION
	'''
	assert open_time(174.5, BREVET_DISTANCES[0], START_TIME) == START_TIME.shift(minutes=309)


def test_incorrect_longer_than_brev_1():
	''' 
	Should not use the 205km to compute the final control open time 
	Incorrect implementation gives: control at 205 --> 5H53 + 0H09 = 362 mins
	'''
	assert not open_time(205, BREVET_DISTANCES[0], START_TIME) == START_TIME.shift(minutes=362)


def test_incorrect_open_calculation():
	'''
	A misunderstanding of the algorithm is: use one interval's speed for
	the entire distance to get the time to be added.

	Incorrect implementation gives: control at 700 --> 25H00 = 1500 mins
	'''
	assert not open_time(700, BREVET_DISTANCES[4], START_TIME) == START_TIME.shift(minutes=1500)



################
# close_time tests
#	Specifically testing the close_time function with 
#	differnt values.
#
# close_time(control_dist_km, brevet_dist_km, brevet_start_time)
################



def test_start_point_close():
	''' Should return: official start time + 1 hr '''
	assert close_time(0, BREVET_DISTANCES[0], START_TIME) == START_TIME.shift(minutes=60)


def test_first_interval_close():
	''' 
	Min speed for control 0 <= dist <= 600 is 15km/hr 
	Control at 550 --> 36H40 = 2200 mins
	'''
	assert close_time(550, BREVET_DISTANCES[3], START_TIME) == START_TIME.shift(minutes=2200)


def test_second_interval_close():
	'''
	Min speed for control 600 < dist <= 1000 is 11.428 
	Control at 890 --> 65H23 = 3923 mins
	'''
	assert close_time(890, BREVET_DISTANCES[4], START_TIME) == START_TIME.shift(minutes=3923)


def test_equal_to_brevet_close():
	''' 
	Should return start time + time limit 
	Control at 400 for 400 brevet --> 27H00 = 1620 mins
	'''
	assert close_time(400, BREVET_DISTANCES[2], START_TIME) == START_TIME.shift(minutes=1620)


def test_longer_than_brevet_close():
	''' 
	Close time for the final brevet is governed by the type of 
	brevet, not by the actual distance.

	Official time limits (km, hr): (200,13H30), (300, 20H00),
	(400, 27H00), (600, 40H00), (1000, 75H00)
	'''
	assert close_time(415, BREVET_DISTANCES[2], START_TIME) == START_TIME.shift(minutes=1620)


def test_short_control():
	'''
	An oddity is that a short control will give a closing time 
	EARLIER than the closing time of the starting point (because 
	of the 1hr default closing time at the start). 

	Note: An above test assures us the close time at 0 is correct.
	Control at 10 --> 0H40 close time < 1H00 close time of starting point
	'''
	assert close_time(10, BREVET_DISTANCES[0], START_TIME) < close_time(0, BREVET_DISTANCES[0], START_TIME)	


def test_decimal_distance_3():
	''' distances should be rounded to nearest km '''
	assert close_time(550.3, BREVET_DISTANCES[3], START_TIME) == START_TIME.shift(minutes=2200)


def test_decimal_distance_4():
	''' distances should be rounded to nearest km '''
	assert close_time(549.7, BREVET_DISTANCES[3], START_TIME) == START_TIME.shift(minutes=2200)


def test_incorrect_short_control():
	'''
	An incorrect implementation will make all closing times later/or equal
	to the starting point's closing time.
	'''
	assert not close_time(10, BREVET_DISTANCES[0], START_TIME) >= close_time(0, BREVET_DISTANCES[0], START_TIME)


def test_incorrect_longer_than_brev_2():
	''' 
	Should not use the 205km to compute the final control close time 
	Incorrect implementation gives: control at 205 --> 13H40 = 820 mins
	'''
	assert not close_time(205, BREVET_DISTANCES[0], START_TIME) == START_TIME.shift(minutes=820)


def test_incorrect_close_calculation():
	'''
	A misunderstanding of the algorithm is: use one interval's speed for
	the entire distance to get the time to be added.

	Incorrect implementation gives: control at 700 --> 61H15 = 2800 mins
	'''
	assert not close_time(700, BREVET_DISTANCES[4], START_TIME) == START_TIME.shift(minutes=2800)





