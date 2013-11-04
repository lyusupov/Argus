# $Id: 80211.py 53 2008-12-18 01:22:57Z jon.oberheide $

"""IEEE 802.11. Management frames """

import dpkt

_MAX_SSID_SIZE      = 32
_MIN_FRAME_SIZE     = 12
_MAX_RATES_SIZE     = 8
_OUI_SIZE           = 3
_MAX_VENDOR_SIZE    = 255 - _OUI_SIZE

# Capability
CAP_ESS             = 0
CAP_IBSS            = 1
CAP_CF_POLLABLE     = 2
CAP_CF_POLL_REQ     = 3
CAP_PRIVACY         = 4
CAP_SHORT_REAMBLE   = 5
CAP_PBCC            = 6
CAP_CHANNEL_AGILITY = 7
CAP_SPECTRUM_MGMT   = 8
CAP_QoS             = 9
CAP_SHORT_SLOT_TIME = 10
CAP_APSD            = 11
CAP_RADIO_MEASMNT   = 12
CAP_DSSS_OFDM       = 13
CAP_DELAYED_BLK_ACK = 14
CAP_IMMED_BLK_ACK   = 15


# Bitshifts for Capability
_ESS_MASK           = 0x1
_ESS_SHIFT          = 0

# Element IDs
_EID_ESSID          = 0
_EID_RATES_SUP      = 1
_EID_DSSS           = 3
_EID_VENDOR         = 0xDD

class IEEE80211_beacon(dpkt.Packet):
    __byte_order__ = '<'
    __hdr__ = (
        ('timestamp', 'Q', 0) ,
        ('interval', 'H', 0) ,
        ('capability', 'H', 0)
        )

    def _get_ess(self): return (self.capability & _ESS_MASK) >> _ESS_SHIFT
    def _set_ess(self, val): self.capability = (val << _ESS_SHIFT) | (self.capability & ~_ESS_MASK)

    ess_present = property(_get_ess, _set_ess)
#    ess_present = 1
    rates_present = ess_present
    dsss_present = ess_present
    vendor_present = ess_present

    def unpack(self, buf):
        dpkt.Packet.unpack(self, buf)
#        self.data = buf[self.length:]
        
        self.fields = []
        buf = buf[self.__hdr_len__:]

        # decode each field into self.<name> (eg. self.tsft) as well as append it self.fields list
        field_decoder = [
            ('essid', self.ess_present, self.ESS),
            ('rates', self.rates_present, self.Rates),
            ('dsss', self.dsss_present, self.DSSS),
            ('vendor', self.vendor_present, self.Vendor),
        ]
        for name, present_bit, parser in field_decoder:
            if present_bit:
                field = parser(buf)
                field.data = ''
                setattr(self, name, field)
                self.fields.append(field)
                buf = buf[len(field):]
                #print " %x " % field.length
                buf = buf[field.length:]

    class ESS(dpkt.Packet):
        __hdr__ = (
            ('eid', 'B',  0),
            ('length', 'B',  0),
            )
        def unpack(self, buf):
            dpkt.Packet.unpack(self, buf)
#            if self.length > _MAX_SSID_SIZE:
#                self.length = _MAX_SSID_SIZE
            self.ssid = 'VERY_BAD_SSID'
            if self.length <= _MAX_SSID_SIZE:
                self.data = self.ssid = self.data[:self.length]

    class Rates(dpkt.Packet):
        __hdr__ = (
            ('eid', 'B',  0),
            ('length', 'B',  0),
            )
        def unpack(self, buf):
            dpkt.Packet.unpack(self, buf)
            self.rates_map = ''
            if self.length <= _MAX_RATES_SIZE:
                self.data = self.rates_map = self.data[:self.length]

    class DSSS(dpkt.Packet):
        __hdr__ = (
            ('eid', 'B',  0),
            ('length', 'B',  0),
            #('channel', 'B',  0),
            )

    class Vendor(dpkt.Packet):
        __hdr__ = (
            ('eid', 'B',  0),
            ('length', 'B',  0),
            #('oui', '3s', '\x00' * 3)
            )
        def unpack(self, buf):
            dpkt.Packet.unpack(self, buf)
            self.space = ''
            if self.length <= _MAX_VENDOR_SIZE:
                self.data = self.space = self.data[:self.length]

if __name__ == '__main__':
    import unittest
    
    class IEEE80211TestCase(unittest.TestCase):
        def test_802211(self):
            s = '\xd4\x00\x00\x00\x00\x12\xf0\xb6\x1c\xa4'
            ieee = IEEE80211(s)
            self.failUnless(str(ieee) == s)
            self.failUnless(ieee.version == 0)
            self.failUnless(ieee.type == CONTROL)
            self.failUnless(ieee.subtype == C_ACK)
            self.failUnless(ieee.to_ds == 0)
            self.failUnless(ieee.from_ds == 0)
            self.failUnless(ieee.pwr_mgt == 0)
            self.failUnless(ieee.more_data == 0)
            self.failUnless(ieee.wep == 0)
            self.failUnless(ieee.order == 0)
            self.failUnless(ieee.ack.dst == '\x00\x12\xf0\xb6\x1c\xa4')

    unittest.main()

