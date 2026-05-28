class Rules:

  # Contact (poly/diff to metal1)
  contact_size      = 0.22    # contact minimum size
  contact_spacing   = 0.28    # contact-to-contact spacing
  comp_cont_enc     = 0.07    # diffusion enclosure of contact
  implant_cmp_enc   = 0.16    # implant enclosure of diffusion
  cont2poly         = 0.15    # contact to poly spacing
  poly_ext_cmp      = 0.22    # poly extension beyond diffusion
  np_enc_gate       = 0.23    # nplus gate enclosure

  # Metal1
  metal1_width      = 0.23    # metal1 minimum width
  metal1_spacing    = 0.23    # metal1 minimum spacing
  met1_cont_enc     = 0.06    # metal1 enclosure of contact

  # Via1 (metal1 to metal2)
  via1_size         = 0.26
  via1_spacing      = 0.50
  met1_via1_enc     = 0.40
  met2_via1_enc     = 0.40

  # Via2 (metal2 to metal3)
  via2_size         = 0.26
  via2_spacing      = 0.50
  met2_via2_enc     = 0.40
  met3_via2_enc     = 0.40

  # Via3 (metal3 to metal4)
  via3_size         = 0.26
  via3_spacing      = 0.50
  met3_via3_enc     = 0.40
  met4_via3_enc     = 0.40

  # Via4 (metal4 to metal5)
  via4_size         = 0.26
  via4_spacing      = 0.50
  met4_via4_enc     = 0.40
  met5_via4_enc     = 0.40

  # Via5 (metal5 to metaltop)
  via5_size         = 0.26
  via5_spacing      = 0.50
  met5_via5_enc     = 0.40
  mtop_via5_enc     = 0.40

  # Metal widths
  metal2_width      = 0.28
  metal3_width      = 0.28
  metal4_width      = 0.28
  metal5_width      = 0.28
  metaltop_width    = 0.28

  # Poly
  poly_width        = 0.18
  poly_spacing      = 0.18

  # Diffusion
  diff_width        = 0.22
  diff_diff_spc     = 0.32    # diffusion-to-diffusion spacing
  diff_diff_spc_hi  = 0.36    # for 5V/6V / deepnwell

  # Nwell
  nwell_width       = 0.42

  # Implant / SDP
  nplus_pplus_spc   = 0.48    # n+/p+ spacing
  pplus_width       = 0.36    # p+ minimum width (guard ring)

  # 5V/6V device structures
  dnwell_enc_lvpwell = 2.5    # DNWELL enclosure of LVPWELL
  lvpwell_enc_ncomp  = 0.6    # LVPWELL enclosure of n-comp (5V/6V)
  lvpwell_enc_pcomp  = 0.16   # LVPWELL enclosure of p-comp (5V/6V)
  lvpwell_enc_ncomp_3v3 = 0.43  # LVPWELL enclosure of n-comp (3.3V)
  lvpwell_enc_pcomp_3v3 = 0.12  # LVPWELL enclosure of p-comp (3.3V)
  dg_enc_dnwell      = 0.5    # dualgate enclosure of DNWELL
  dg_enc_ply         = 0.4    # dualgate poly enclosure
  dg_enc_cmp         = 0.24   # dualgate comp enclosure
  pcmp_gr2dnw        = 2.5    # p+ guard ring to DNWELL spacing

  # Guard ring
  gr_width           = 0.36   # guard ring minimum width
  poly_gr_spc        = 0.30   # poly to guard ring spacing (5V/6V/dnw)
  poly_gr_spc_3v3    = 0.26   # poly to guard ring spacing (3.3V)

  # MOS capacitor
  cmp_poly_enc       = 0.44   # diffusion enclosure of poly (cap)
  poly_ext           = 0.46   # poly extension beyond diffusion (cap)
  cmp_cont_poly_spc  = 0.17   # comp to contact/poly spacing (cap)
  dualgate_cmp_enc_x = 0.96   # dualgate comp enclosure x (cap)
  dualgate_cmp_enc_y = 1.36   # dualgate comp enclosure y (cap)
  met1_cont_enc      = 0.06   # metal1 enclosure of contact (cap)
  met_con_min        = 0.34   # metal contact side minimum (cap)

  # MIM capacitor
  mim_top_bot_enc    = 0.60   # top/bottom metal enclosure (MIM)
  mim_via_size       = 0.26   # via size over MIM
  mim_via_spacing    = 0.50   # via spacing over MIM
  mim_met_via_enc    = 0.40   # metal enclosure of MIM via

  # Resistor
  cmp_res_enc        = 0.29   # comp enclosure around resistor region
  ncmp_pcmp_spc      = 0.72   # n-comp to p-comp spacing (resistor)
  cmp_met_cont_enc_diff = 0.01  # comp/metal/contact enclosure diff

  # Metal resistor types
  rm1_enc            = 0.23
  rm2_enc            = 0.28
  rm3_enc            = 0.28
  tm6k_enc           = 0.36
  tm9k_enc           = 0.44
  tm11k_enc          = 0.44
  tm30k_enc          = 1.80

  # Minimum areas
  min_cmp_area       = 0.2025  # minimum diffusion area

  # Diffusion length
  ld_min             = 0.44   # minimum diffusion length

  # FET minimum dimensions
  # 3.3V
  nfet_3v3_l         = 0.28   # minimum gate length
  nfet_3v3_w         = 0.22   # minimum finger width
  pfet_3v3_l         = 0.28
  pfet_3v3_w         = 0.22
  # 5V
  nfet_5v_l          = 0.60
  nfet_5v_w          = 0.30
  pfet_5v_l          = 0.50
  pfet_5v_w          = 0.30
  # 6V
  nfet_6v_l          = 0.70
  nfet_6v_w          = 0.30
  pfet_6v_l          = 0.55
  pfet_6v_w          = 0.30

  # Natural channel FET
  nfet_nat_l         = 1.80
  nfet_nat_w         = 0.80
  ldfet_l_min        = 0.60
  ldfet_l_max        = 20.0
  ldfet_w_min        = 4.0
  ldfet_w_max        = 50.0

  # Diode minimums
  diode_l            = 0.36
  diode_w            = 0.22
  sc_diode_l         = 1.0
  sc_diode_w         = 0.62

  # MOS capacitor minimums
  cap_nmos_l         = 1.0
  cap_nmos_w         = 1.88
  cap_pmos_l         = 1.0
  cap_pmos_w         = 1.88

  # MIM capacitor minimums
  mim_l              = 0.28
  mim_w              = 0.28

  # Resistor minimums
  nplus_s_l          = 0.42
  nplus_s_w          = 0.42
  pplus_s_l          = 0.42
  pplus_s_w          = 0.42
  nplus_u_l          = 0.42
  nplus_u_w          = 0.42
  pplus_u_l          = 0.42
  pplus_u_w          = 0.42
  nwell_l            = 0.42
  nwell_w            = 0.42
  pwell_l            = 0.42
  pwell_w            = 0.42
  npolyf_s_l         = 0.42
  npolyf_s_w         = 0.42
  ppolyf_s_l         = 0.42
  ppolyf_s_w         = 0.42
  npolyf_u_l         = 0.42
  npolyf_u_w         = 0.42
  ppolyf_u_l         = 0.42
  ppolyf_u_w         = 0.42
  rm1_l              = 0.23
  rm1_w              = 0.23
  rm2_l              = 0.28
  rm2_w              = 0.28
  tm6k_l             = 0.36
  tm6k_w             = 0.36
  tm9k_l             = 0.44
  tm9k_w             = 0.44
  tm30k_l            = 1.80
  tm30k_w            = 1.80
