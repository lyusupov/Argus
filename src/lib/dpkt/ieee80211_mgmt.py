# $Id: 80211.py 53 2008-12-18 01:22:57Z jon.oberheide $

"""IEEE 802.11. Management frames """

import dpkt

# Frame Types
MANAGEMENT          = 0
CONTROL             = 1
DATA                = 2

# Frame Sub-Types
M_ASSOC_REQ         = 0
M_ASSOC_RESP        = 1
M_REASSOC_REQ       = 2
M_REASSOC_RESP      = 3
M_PROBE_REQ         = 4
M_PROBE_RESP        = 5
M_TIMING_ADVT       = 6
M_BEACON            = 8
M_ATIM              = 9
M_DISASSOC          = 10
M_AUTH              = 11
M_DEAUTH            = 12
M_ACTION            = 13
C_PS_POLL           = 10
C_RTS               = 11
C_CTS               = 12
C_ACK               = 13
C_CF_END            = 14
C_CF_END_ACK        = 15
D_DATA              = 0
D_DATA_CF_ACK       = 1
D_DATA_CF_POLL      = 2
D_DATA_CF_ACK_POLL  = 3
D_NULL              = 4
D_CF_ACK            = 5
D_CF_POLL           = 6
D_CF_ACK_POLL       = 7

# Bitshifts for Frame Control
_VERSION_MASK       = 0x0300
_TYPE_MASK          = 0x0c00
_SUBTYPE_MASK       = 0xf000
_TO_DS_MASK         = 0x0001
_FROM_DS_MASK       = 0x0002
_MORE_FRAG_MASK     = 0x0004
_RETRY_MASK         = 0x0008
_PWR_MGT_MASK       = 0x0010
_MORE_DATA_MASK     = 0x0020
_WEP_MASK           = 0x0040
_ORDER_MASK         = 0x0080
_VERSION_SHIFT      = 8
_TYPE_SHIFT         = 10
_SUBTYPE_SHIFT      = 12
_TO_DS_SHIFT        = 0
_FROM_DS_SHIFT      = 1
_MORE_FRAG_SHIFT    = 2
_RETRY_SHIFT        = 3
_PWR_MGT_SHIFT      = 4
_MORE_DATA_SHIFT    = 5
_WEP_SHIFT          = 6
_ORDER_SHIFT        = 7

class IEEE80211_mgmt(dpkt.Packet):
    __hdr__ = (
        ('framectl', 'H', 0),
        ('duration', 'H', 0)
        )

    def _get_version(self): return (self.framectl & _VERSION_MASK) >> _VERSION_SHIFT
    def _set_version(self, val): self.framectl = (val << _VERSION_SHIFT) | (self.framectl & ~_VERSION_MASK)
    def _get_type(self): return (self.framectl & _TYPE_MASK) >> _TYPE_SHIFT
    def _set_type(self, val): self.framectl = (val << _TYPE_SHIFT) | (self.framectl & ~_TYPE_MASK)
    def _get_subtype(self): return (self.framectl & _SUBTYPE_MASK) >> _SUBTYPE_SHIFT
    def _set_subtype(self, val): self.framectl = (val << _SUBTYPE_SHIFT) | (self.framectl & ~_SUBTYPE_MASK)
    def _get_order(self): return (self.framectl & _ORDER_MASK) >> _ORDER_SHIFT
    def _set_order(self, val): self.framectl = (val << _ORDER_SHIFT) | (self.framectl & ~_ORDER_MASK)
    def _get_length(self):
        if (self.order == 1):
          return 28
        else:
          return 24

    version = property(_get_version, _set_version)
    type = property(_get_type, _set_type)
    subtype = property(_get_subtype, _set_subtype)
    order = property(_get_order, _set_order)
    length = property(_get_length)

    def unpack(self, buf):
        dpkt.Packet.unpack(self, buf)
        self.data = buf[self.__hdr_len__:]

        if self.type == MANAGEMENT:
          try:
            if self.order == 1:
                self.data = self.ManagementHT(self.data)
            else:
                self.data = self.Management(self.data)
          except (KeyError, dpkt.UnpackError):
            self.data = buf

    class Management(dpkt.Packet):
        __hdr__ = (
            ('address1', '6s', '\x00' * 6),
            ('address2', '6s', '\x00' * 6),
            ('address3', '6s', '\x00' * 6),
            ('sequence', 'H', 0),
            )

    class ManagementHT(dpkt.Packet):
        __hdr__ = (
            ('address1', '6s', '\x00' * 6),
            ('address2', '6s', '\x00' * 6),
            ('address3', '6s', '\x00' * 6),
            ('sequence', 'H', 0),
            ('ht', 'I', 0)
            )

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

