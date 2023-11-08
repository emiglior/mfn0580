import array

def read_file(input_filename):
    times = array.array('d')
    codes = array.array('d')

    f = open(input_filename, 'r')
    for _line in f:
        s0, s1 =  _line.split(",")
        times.append( float(s0) )
        codes.append( float(s1) )
    f.close()
    return times, codes
