"""
Open and close time calculations
for ACP-sanctioned brevets
following rules described at https://rusa.org/octime_alg.html
and https://rusa.org/pages/rulesForRiders
"""
import arrow
import math

#####
# For ease of use, all time to be added will be represented in minutes as an int.
# We use an int because all time is rounded to the nearest minute 
# (as specified in the time calculation instructions on https://rusa.org/octime_alg.html). 
#####

def better_round(num):
  '''
  Python round function doesn't round correctly for even 
  numbers and a half. i.e. for any even number e, 
  round(e.5) = e instead of e+1. 

  This function corrects that feature.
  '''
  val = num - math.floor(num) + 1.0
  rval = round(val)
  if (rval == 2):
    return math.ceil(num)
  else:
    return math.floor(num)


# Governed by MAX SPEED
def open_time(control_dist_km, brevet_dist_km, brevet_start_time):
    """
    Args:
       control_dist_km:  number, the control distance in kilometers
       brevet_dist_km: number, the nominal distance of the brevet
           in kilometers, which must be one of 200, 300, 400, 600,
           or 1000 (the only official ACP brevet distances)
       brevet_start_time:  An ISO 8601 format date-time string indicating
           the official start time of the brevet
    Returns:
       An ISO 8601 format date string indicating the control open time.
       This will be in the same time zone as the brevet start time.
    """
    # list of tuples: (dist_lower_bound, max_speed) --> UNITS: (km, km/hr)
    # descending order for ease of iteration
    max_speed_bound = [(600, 28), (400, 30), (200, 32), (0, 34)]
    add_time = 0  # time added to brevet_start_time
    dist = 0      # keep track of remaining distance

    if (control_dist_km == 0):
      return brevet_start_time
    else:
      if(control_dist_km > brevet_dist_km):
        dist = brevet_dist_km     # if greater, use theoretical distance (which is an int)
      else:
        dist = better_round(control_dist_km)    # otherwise, use control dist rounded to nearest km

      for bound in max_speed_bound:
        (mins, margin) = (0.0, 0.0)
        if (dist > bound[0]):           # Notice, if distance == bound[0] it is in lower interval
          margin = dist - bound[0]
          dist = bound[0]
          mins = (margin/bound[1])*60
          add_time += better_round(mins)

      return brevet_start_time.shift(minutes=add_time)


# Governed by MIN SPEED
def close_time(control_dist_km, brevet_dist_km, brevet_start_time):
    """
    Args:
      control_dist_km: number, the control distance in kilometers
      brevet_dist_km: number, the nominal distance of the brevet
          in kilometers, which must be one of 200, 300, 400, 600, or 1000
          (the only official ACP brevet distances)
      brevet_start_time:  An ISO 8601 format date-time string indicating
           the official start time of the brevet
    Returns:
       An ISO 8601 format date string indicating the control close time.
       This will be in the same time zone as the brevet start time.
    """
    # dict of time limits --> brevet_dist_km : time_limit_to_complete ---- UNITS: (km, minutes)
    brev_time_limit = {200:810, 300:1200, 400:1620, 600:2400, 1000:4500} 
    # list of tuples: (dist_lower_bound, min_speed) --> UNITS: (km, km/hr)
    min_speed_bound = [(600, 11.428), (0, 15)]  
    add_time = 0  # time added to brevet_start_time
    dist = 0      # keep track of remaining distance

    if (control_dist_km == 0):
      # Close time of starting point is 1 hr after start time
      return brevet_start_time.shift(minutes=60)   
    elif (control_dist_km >= brevet_dist_km):
      # Look up time limit in dict and return start time + time limit
      add_time = brev_time_limit[brevet_dist_km]
      return brevet_start_time.shift(minutes=add_time)
    else:
      dist = better_round(control_dist_km)    # otherwise, use control dist rounded to nearest km

      for bound in min_speed_bound:
        (mins, margin) = (0.0, 0.0)
        if (dist > bound[0]):
          margin = dist - bound[0]
          dist = bound[0]
          mins = (margin/bound[1])*60
          add_time += better_round(mins)

      return brevet_start_time.shift(minutes=add_time)


      

