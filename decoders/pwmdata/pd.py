##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2014 Torsten Duwe <duwe@suse.de>
## Copyright (C) 2014 Sebastien Bourdelin <sebastien.bourdelin@savoirfairelinux.com>
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, see <http://www.gnu.org/licenses/>.
##

import sigrokdecode as srd

class Decoder(srd.Decoder):
    api_version = 3
    id = 'pwmdata'
    name = 'PWM Data'
    longname = 'Pulse-width modulation'
    desc = 'Extract digital data from PWM.'
    license = 'gplv2+'
    inputs = ['pwm']
    outputs = []
    tags = ['Encoding']
    options = (

    )
    annotations = (
        ('preamble', 'Preamble'),
        ('bits', 'Bits'),
        ('bytes', 'Bytes'),
    )
    annotation_rows = (
        ('control', 'Control', (0,)),
        ('data', 'Data', (1, 2)),
    )
    binary = (
        ('bits', 'Bits'),
        ('bytes', 'Bytes'),
    )

    def __init__(self):
        import sys
        sys.path.insert(0, 'C:/Users/antonio.vazquez/AppData/Roaming/Python/Python310/site-packages')
        import rpdb2
        #rpdb2.start_embedded_debugger("pd", fAllowRemote=True)
        self.reset()

    def reset(self):
        self.state = 'wait_preamble'

    def metadata(self, key, value):
        if key == srd.SRD_CONF_SAMPLERATE:
            self.samplerate = value

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)
        self.out_binary = self.register(srd.OUTPUT_BINARY)

    def put_control(self, ss, es, data):
        self.put(ss, es, self.out_ann, [0, [data]])

    def put_bit(self, ss, es, bit):
        self.put(ss, es, self.out_ann, [1, ["1" if bit else "0"]])
        self.put(ss, es, self.out_binary, [0, b'\x01' if bit else b'\x00'])

    def validate_preamble_period(self, period):
        return 500/(1000*1000) <= period <= 1/1000

    def handle_wait_preamble(self, ss, es, period, duty):
        if not hasattr(self, 'preamble_samples'):
            self.preamble_samples = 0
        if self.validate_preamble_period(period):
            if self.preamble_samples == 0:
                self.preamble_start = ss
            self.preamble_samples += 1
            return
        # Did we go around enough samples and this is the wait?
        if self.preamble_samples < 5 or period < 1/1000:
            # Not enough preamble bits or wait to short, discard...
            self.preamble_samples = 0
            return
        # We are in the wait sample after the preamble
        self.put_control(self.preamble_start, es, "Preamble")
        self.preamble_samples = 0
        self.received_bits = 0
        self.state = 'receive'

    def handle_receive(self, ss, es, period, duty):
        self.received_bits += 1
        if self.received_bits == 66:
            self.state = 'wait_preamble'
            es = int(ss+1.2/1000*self.samplerate)
        self.put_bit(ss, es, duty < 0.6/1000)

    def decode(self, ss, es, data):
        # Packet format is [period, period_seconds, duty_ratio]
        _, period, _, duty, _ = data
        # State machine.
        s = 'handle_%s' % self.state.lower().replace(' ', '_')
        handle_state = getattr(self, s)
        handle_state(ss, es, period, duty)
        
