##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2019 Antonio Vázquez Blanco <antoniovazquezblanco@gmail.com>
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
from .ezbl_state import EzblState
from .annotation_messages import AnnotationMessages

class Decoder(srd.Decoder):
    api_version = 3
    id = 'microchip_ezbl'
    name = 'Microchip EZBL'
    longname = 'Microchip EZBL'
    desc = 'Microchip EZBL bootloader communication protocol.'
    license = 'gplv3+'
    inputs = ['uart']
    outputs = []
    tags = ['Microchip/bootloader']
    annotations = (
        ('mosi-data', 'MOSI data'),
        ('miso-data', 'MISO data'),
        ('warnings', 'Warnings'),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.state = EzblState.WAIT
        self.offer_sync_buf = ''
        self.offer_sync_start_sample = -1
        self.offer_fileid_buf = ''
        self.offer_fileid_start_sample = -1
        self.offer_filelen_buf = []
        self.offer_filelen_start_sample = -1
        self.offer_bootidhash_buf = ''
        self.offer_bootidhash_start_sample = -1
        self.offer_appidver_buf = []
        self.offer_appidver_start_sample = -1
        self.offer_hmac_buf = ''
        self.offer_hmac_start_sample = -1
        self.timeout_master_sample = -1
        self.timeout_slave_sample = -1
        self.uc_message = []
        

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)
        
    def decode(self, start_sample, end_sample, data):
        # Split data
        packet_type, packet_is_mosi, packet = data

        # Filter out non data packets
        if packet_type != 'DATA':
            return

        # Get packet payload
        packet_payload = packet[0]
        
        # Protocol handled as a state machine
        while True:
            if self.state == EzblState.WAIT:
                # Here, the uC is waiting for a master packet containing a fw offering
                if packet_is_mosi:
                    # If master sends something, store the start time of the offer and
                    # evolve to the offer sync state
                    self.offer_sync_start_sample = start_sample
                    self.state = EzblState.OFFER_SYNC
                    # Do not return to process the next state
                else:
                    # If the packet did not come from the master warn the user
                    self._put_warning_annotation(start_sample, end_sample, AnnotationMessages.UNEXPECTED_MISO)
                    # Wait for the next packet
                    return
            elif self.state == EzblState.OFFER_SYNC:
                # Expecting master sync header
                if not packet_is_mosi:
                    # If the packet did not come from the master warn the user
                    self._put_warning_annotation(start_sample, end_sample, AnnotationMessages.UNEXPECTED_MISO)
                    # Wait for the next packet
                    return
                # Store master bytes as a string
                self.offer_sync_buf += chr(packet_payload)
                # Check if we have enought data for the header
                if len(self.offer_sync_buf) < 16:
                    # Not enought data, return to wait for more
                    return
                # Check the message 
                if self.offer_sync_buf != 'UUUUUUUUMCUPHCME':
                    # Wrong
                    self._put_warning_annotation(start_sample, end_sample, AnnotationMessages.SYNC_MESSAGE_WRONG)
                    # Reset everything
                    self.reset()
                    # Start again
                    return
                # Correct sync message
                self._put_mosi_annotation(self.offer_sync_start_sample, end_sample, AnnotationMessages.SYNC_MESSAGE)
                # Store the start time of the filed id message
                self.offer_fileid_start_sample = end_sample
                # Evolve to the next state
                self.state = EzblState.OFFER_FILEID
                # Return to wait for a packet
                return
            elif self.state == EzblState.OFFER_FILEID:
                # Expecting master fileid header
                if not packet_is_mosi:
                    # If the packet did not come from the master warn the user
                    self._put_warning_annotation(start_sample, end_sample, AnnotationMessages.UNEXPECTED_MISO)
                    # Wait for the next packet
                    return
                # Store master bytes as a string
                self.offer_fileid_buf += chr(packet_payload)
                # Check if we have enought data for the header
                if len(self.offer_fileid_buf) < 4:
                    # Not enought data, return to wait for more
                    return
                # Check the message 
                if self.offer_fileid_buf != 'BL2B':
                    # Wrong
                    self._put_warning_annotation(start_sample, end_sample, AnnotationMessages.FILEID_MESSAGE_WRONG)
                    # Reset everything
                    self.reset()
                    # Start again
                    return
                # Correct file id message
                self._put_mosi_annotation(self.offer_fileid_start_sample, end_sample, AnnotationMessages.FILEID_MESSAGE)
                # Store the start time of the filed id message
                self.offer_filelen_start_sample = end_sample
                # Evolve to the next state
                self.state = EzblState.OFFER_FILELEN
                # Return to wait for a packet
                return
            elif self.state == EzblState.OFFER_FILELEN:
                # Expecting master fileid header
                if not packet_is_mosi:
                    # If the packet did not come from the master warn the user
                    self._put_warning_annotation(start_sample, end_sample, AnnotationMessages.UNEXPECTED_MISO)
                    # Wait for the next packet
                    return
                # Store master bytes as an array
                self.offer_filelen_buf.append(packet_payload)
                # Check if we have enought data
                if len(self.offer_filelen_buf) < 4:
                    # Not enought data, return to wait for more
                    return
                # Convert message
                self.file_length = int.from_bytes(self.offer_filelen_buf, byteorder='little')
                # Show file length
                self._put_mosi_annotation(self.offer_filelen_start_sample, end_sample, AnnotationMessages.format(AnnotationMessages.FILELEN_MESSAGE, self.file_length))
                # Store the start time of the bootidhash message
                self.offer_bootidhash_start_sample = end_sample
                # Evolve to the next state
                self.state = EzblState.OFFER_BOOTIDHASH
                # Return to wait for a packet
                return
            elif self.state == EzblState.OFFER_BOOTIDHASH:
                # Expecting master fileid header
                if not packet_is_mosi:
                    # If the packet did not come from the master warn the user
                    self._put_warning_annotation(start_sample, end_sample, AnnotationMessages.UNEXPECTED_MISO)
                    # Wait for the next packet
                    return
                # Store master bytes as an array
                self.offer_bootidhash_buf += '{:02x}'.format(packet_payload)
                # Check if we have enought data
                if len(self.offer_bootidhash_buf) < 32:
                    # Not enought data, return to wait for more
                    return
                # Show hash
                self._put_mosi_annotation(self.offer_bootidhash_start_sample, end_sample, AnnotationMessages.format(AnnotationMessages.BOOTIDHASH_MESSAGE, self.offer_bootidhash_buf))
                # Store the start time of the appidver message
                self.offer_appidver_start_sample = end_sample
                # Evolve to the next state
                self.state = EzblState.OFFER_APPIDVER
                # Return to wait for a packet
                return
            elif self.state == EzblState.OFFER_APPIDVER:
                # Expecting master fileid header
                if not packet_is_mosi:
                    # If the packet did not come from the master warn the user
                    self._put_warning_annotation(start_sample, end_sample, AnnotationMessages.UNEXPECTED_MISO)
                    # Wait for the next packet
                    return
                # Store master bytes as an array
                self.offer_appidver_buf.append(packet_payload)
                # Check if we have enought data
                if len(self.offer_appidver_buf) < 8:
                    # Not enought data, return to wait for more
                    return
                # Convert message
                ver_build = int.from_bytes(self.offer_appidver_buf[0:3], byteorder='little')
                ver_minor = int.from_bytes(self.offer_appidver_buf[4:5], byteorder='little')
                ver_major = int.from_bytes(self.offer_appidver_buf[6:7], byteorder='little')
                version = 'v{}.{}.{}'.format(ver_major, ver_minor, ver_build)
                # Show file length
                self._put_mosi_annotation(self.offer_appidver_start_sample, end_sample, AnnotationMessages.format(AnnotationMessages.APPIDVER_MESSAGE, version))
                # Store the start time of the bootidhash message
                self.offer_hmac_start_sample_start_sample = end_sample
                # Evolve to the next state
                self.state = EzblState.OFFER_HMACSHA256
                # Return to wait for a packet
                return
            elif self.state == EzblState.OFFER_HMACSHA256:
                # Expecting master fileid header
                if not packet_is_mosi:
                    # If the packet did not come from the master warn the user
                    self._put_warning_annotation(start_sample, end_sample, AnnotationMessages.UNEXPECTED_MISO)
                    # Wait for the next packet
                    return
                # Store master bytes as an string
                self.offer_hmac_buf += '{:02x}'.format(packet_payload)
                # Check if we have enought data
                if len(self.offer_hmac_buf) < 32:
                    # Not enought data, return to wait for more
                    return
                # Show hash
                self._put_mosi_annotation(self.offer_hmac_start_sample_start_sample, end_sample, AnnotationMessages.format(AnnotationMessages.HMAC_MESSAGE, self.offer_hmac_buf))
                # Store the last time anything was known about the master
                self.timeout_master_sample = end_sample
                # Evolve to the next state
                self.state = EzblState.WAIT_UC_RESPONSE
                # Return to wait for a packet
                return
            elif self.state == EzblState.WAIT_UC_RESPONSE:
                # Expecting slave message
                if packet_is_mosi:
                    # If the packet did not come from the master warn the user
                    self._put_warning_annotation(start_sample, end_sample, AnnotationMessages.UNEXPECTED_MOSI)
                    # Wait for the next packet
                    return
                # Store slave bytes as an array
                self.uc_message.append(packet_payload)
                print(packet_payload)
                # Check if we have enought data
                if len(self.uc_message) < 2:
                    # Not enought data, return to wait for more
                    return
                # Convert message
                control_code = int.from_bytes(self.uc_message, byteorder='little')
                # Clean uC messages
                self.uc_message = []
                # Check the code
                print(control_code)
                return
                
                
    def _put_annotation(self, start_sample, end_sample, annotation_index, data):
        self.put(start_sample, end_sample, self.out_ann, [annotation_index, data])

    def _put_warning_annotation(self, start_sample, end_sample, data):
        self._put_annotation(start_sample, end_sample, 2, data)

    def _put_mosi_annotation(self, start_sample, end_sample, data):
        self._put_annotation(start_sample, end_sample, 0, data)
