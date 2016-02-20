
import argparse
import rtmidi_python as rtmidi
import PyStepRocker
from PyStepRocker.TMCM import *
from time import sleep


def connect_steprocker(port):

    global args
    debug = False
    if args.debug in ('all', 'motor'):
        debug = True

    while True:
        if not port:
            port = raw_input('What serial port is your StepRocker on?\n')
        try:
            motor = StepRocker(400, port=port, debug=debug)
        except Exception as e:
            print e
            print ''
            port = None
            continue
        break

    print 'Connected to StepRocker on %s' % port
    return motor


def connect_midi(port=0):

    midiin = rtmidi.MidiIn()
    ports = midiin.ports
    numports = len(ports)
    print numports
    print ports

    if numports > 1:
        print 'Found %i available midi ports:' % numports
        for i, port in enumerate(ports):
            print '  Port %i: %s' % (i, port)
        port = raw_input('Type a midi port number to select it')

    # connect automatically if only one port is available
    elif numports == 1:
        print 'Found one available midi port (0): %s' % (ports[0])

    midiin.open_port(port)
    print 'Connected to midi port %s' % port

    midiin.callback = handle_midi_message

    return midiin


def calc_frequency(note):
    '''Returns the frequency corresponding to a midi note number'''

    max_freq = 2048
    freq = ( 2 ** ((note-69) / 12.0) ) * 440
    return int(freq)
    

def handle_midi_message(message, deltatime, data=None):

    # save the currently held notes so we can stop when the last one is released"
    global notestack
    global args
    debug = False
    if args.debug in ('all', 'midi'):
        debug = True
    status, note, velocity = message

    if debug:
        print 'incoming midi: %s' % message

    if velocity > 0 and status == 144:
        notestack.append(note)
        freq = calc_frequency(note)
        if debug:
           print 'output frequency: ' + str(freq)
        motor.TMCL.ror(0, freq)
    elif note == notestack[-1]:
        motor.stop()
        notestack.pop()

    lastnote = note


def cleanup():

    print 'cleaning up...'
    midiin.close_port()
    motor.TMCL._ser.close()
    print 'squeaky clean'


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Play a stepper motor with your midi device')
    parser.add_argument('-s', '--serial', help='port for connecting to a StepRocker')
    parser.add_argument('-m', '--motor', type=int,
                        help='select a motor number (defaults to 0)')
    parser.add_argument('-d', '--debug', type=str, choices={'all', 'motor', 'midi'},
                        help='print debugging messages')
    args = parser.parse_args()

    motor = connect_steprocker(args.serial)
    midiin = connect_midi()
    notestack = []

    motor.TMCL.sap(0, 140, 6)  # set microstep res.
    motor.TMCL.sap(0, 6, 127)  # set current
    motor.TMCL.sap(0, 5, 500)  # set acceleration
    motor.TMCL.ror(0, 1000)
    sleep(1)
    motor.stop()
    
    try:
        while True:
            pass
    except KeyboardInterrupt:
        pass

    cleanup()
