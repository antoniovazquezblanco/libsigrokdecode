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

class AnnotationMessages:
    UNEXPECTED_MISO = ['Unknown slave message']
    UNEXPECTED_MOSI = ['Unknown master message']
    SYNC_MESSAGE_WRONG = ['Wrong synchronization header']
    SYNC_MESSAGE = ['Synchronization header', 'SYNC HDR', 'SYNC']
    FILEID_MESSAGE_WRONG = ['Wrong file id header']
    FILEID_MESSAGE = ['File ID header', 'FILEID HDR', 'FILEID']
    FILELEN_MESSAGE = ['File length: {} bytes', 'FILE LEN: {}b', 'LEN: {}b']
    BOOTIDHASH_MESSAGE = ['Boot ID hash: {}']
    APPIDVER_MESSAGE = ['Application version: {}']
    HMAC_MESSAGE = ['HMAC_SHA_256: {}']
    
    @staticmethod
    def format(msg, params):
        return list(map(lambda x: x.format(params), msg))
