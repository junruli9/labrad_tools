import json
import os

from datetime import date, timedelta
from itertools import chain
from time import strftime

SEQUENCE_DIRECTORY = '/home/bialkali/data/{}/sequences/'
TIMING_CHANNEL = 'Trigger@D15'

def value_to_sequence(sequence):
    if type(sequence.value).__name__ == 'list':

#        # removed KM 3/18/18
#        # the try-except block is nice for error handling but
#        # we'd rather just break conductor if an
#        # incorrect sequence is put in 
#        try: 
#            return combine_sequences([
#                read_sequence_file(sequence.sequence_directory, v) 
#                for v in sequence.value
#            ])
#        except Exception, e:
#            print e
#            return read_sequence_file(sequence.sequence_directory, 'all_off')

        return combine_sequences([
            read_sequence_file(sequence.sequence_directory, v) 
            for v in sequence.value
        ])
    else:
        return value


def read_sequence_file(sequence_directory, filename):
    if type(filename).__name__ == 'dict':
        return filename
    if not os.path.exists(filename):
        for i in range(365):
            day = date.today() - timedelta(i)
            path = sequence_directory.format(day.strftime('%Y%m%d')) + filename
            if os.path.exists(path):
                filename = path
                break
    with open(filename, 'r') as infile:
         sequence = json.load(infile)

    # Get sequence:
    s = {}
    try:
        s = sequence['sequence']
    except KeyError:
        s = sequence

    # Get electrode sequence
    timing = s[TIMING_CHANNEL]
    try:
        electrode_seq = sequence['meta']['electrode']
    except KeyError:
        electrode_seq = []

    # Ensure that electrode sequence has correct length
    if len(electrode_seq) != len(timing):
        electrode_seq = [zero_sequence(v['dt']) for v in s]    

    return (s, electrode_seq)

def zero_sequence(dt):
    return {'dt': dt, 'type': 's', 'vf': 0}

def combine_sequences(sequence_list):
    combined_sequence = sequence_list.pop(0)
    for sequence in sequence_list:
        for k in sequence.keys():
            combined_sequence[k] += sequence[k]
    return combined_sequence

def get_parameters(x):
    """ determine which parameters we need to get from conductor or db """
    if type(x).__name__ in ['str', 'unicode'] and x[0] == '*':
        return [x]
    elif type(x).__name__ == 'list':
        return list(chain.from_iterable([get_parameters(xx) for xx in x]))
    elif type(x).__name__ == 'dict':
        return list(chain.from_iterable([get_parameters(v) for v in x.values()]))
    else:
        return []

def substitute_sequence_parameters(x, parameter_values):
    if type(x).__name__ in ['str', 'unicode']:
        if x[0] == '*':
            return parameter_values[x]
        else:
            return x
    elif type(x).__name__ == 'list':
        return [substitute_sequence_parameters(xx, parameter_values) for xx in x]
    elif type(x).__name__ == 'dict':
        return {k: substitute_sequence_parameters(v, parameter_values) for k, v in x.items()}
    else:
        return x

def get_duration(sequence):
    return max([sum([s['dt'] for s in cs]) for cs in sequence.values()])

