import pya as kdb

class Layers:

  def by_name(name):
    return Layers.__dict__[name]

  dnwell    = kdb.LayerInfo(12, 0)
  nwell     = kdb.LayerInfo(21, 0)
  comp      = kdb.LayerInfo(22, 0)
  esd       = kdb.LayerInfo(24, 0)
  nat       = kdb.LayerInfo(5, 0)
  poly      = kdb.LayerInfo(30, 0)
  pplus     = kdb.LayerInfo(31, 0)
  nplus     = kdb.LayerInfo(32, 0)
  contact   = kdb.LayerInfo(33, 0)
  metal1    = kdb.LayerInfo(34, 0)
  via1      = kdb.LayerInfo(35, 0)
  metal2    = kdb.LayerInfo(36, 0)
  via2      = kdb.LayerInfo(38, 0)
  metal3    = kdb.LayerInfo(42, 0)
  via3      = kdb.LayerInfo(40, 0)
  metal4    = kdb.LayerInfo(46, 0)
  via4      = kdb.LayerInfo(41, 0)
  metal5    = kdb.LayerInfo(81, 0)
  via5      = kdb.LayerInfo(82, 0)
  metaltop  = kdb.LayerInfo(53, 0)
  sab       = kdb.LayerInfo(49, 0)
  lvpwell   = kdb.LayerInfo(204, 0)
  dualgate  = kdb.LayerInfo(55, 0)
  resistor  = kdb.LayerInfo(62, 0)
  fusetop   = kdb.LayerInfo(75, 0)
  schottky  = kdb.LayerInfo(241, 0)

  res_mk    = kdb.LayerInfo(110, 5)
  v5_xtor   = kdb.LayerInfo(112, 1)
  cap_mk    = kdb.LayerInfo(117, 5)
  mos_cap_mk = kdb.LayerInfo(166, 5)
  diode_mk  = kdb.LayerInfo(115, 5)
  mim_l_mk  = kdb.LayerInfo(117, 10)
  efuse_mk  = kdb.LayerInfo(80, 5)
  pr_bndry  = kdb.LayerInfo(0, 0)

  metal1_res = kdb.LayerInfo(110, 11)
  metal2_res = kdb.LayerInfo(110, 12)
  metal3_res = kdb.LayerInfo(110, 13)
  metal4_res = kdb.LayerInfo(110, 14)
  metal5_res = kdb.LayerInfo(110, 15)
  metaltop_res = kdb.LayerInfo(110, 16)
