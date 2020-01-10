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


class EzblState:
    WAIT = 0
    OFFER_SYNC = 1
    OFFER_FILEID = 2
    OFFER_FILELEN = 3
    OFFER_BOOTIDHASH = 4
    OFFER_APPIDVER = 5
    OFFER_HMACSHA256 = 6
    WAIT_UC_RESPONSE = 7