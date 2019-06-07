import os
from cls.utils.dict_utils import dct_put
curDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '/')

def make_dflt_stxm_osa_smplholder_settings_dct(fpath):
	dct = {}
	dct_put(dct, "OSA.CENTER", (0,0))
	dct_put(dct, "OSA.RECT", (-1250,500,1250,-5500))
	dct_put(dct, "OSA_AMBIENT.CENTER", ( -1247.7022682879685, -1595.9402372900463))
	dct_put(dct, "OSA_AMBIENT.RECT", (-2497.7022682879715, 1404.0597627099448, 2.2977317120344196, -4595.9402372900377))
	dct_put(dct, "OSA_CRYO.CENTER", ( -1187.5421670895232, -1000.5925262721269 ))
	dct_put(dct, "OSA_CRYO.RECT", ( -4187.5421670895175, 249.5951432086572, 1812.457832910471, -2250.780195752911))   
	dct_put(dct, "SAMPLE_GONI.CENTER", (320.4466858789624, -651.6853932584269 ))
	dct_put(dct, "SAMPLE_GONI.RADIUS", 1000)
	dct_put(dct, "SAMPLE_GONI.RECT",( -494.5533141210376, -511.68539325842687, 1135.4466858789624, -791.6853932584269))
	dct_put(dct, "SAMPLE_STANDARD.CENTER",(-2550.3974645796065, 2707.6956184038504))
	dct_put(dct, "SAMPLE_STANDARD.RADIUS", 1000)
	dct_put(dct, "SAMPLE_STANDARD.RECT", ( -3365.3974645796065, 2847.6956184038504, -1735.3974645796065, 2567.6956184038504 ))
	dct_put(dct, "SMPL_HLDR.CENTER", ( 0, 2500.0 ))
	dct_put(dct, "SMPL_HLDR.RADIUS", 1000)
	dct_put(dct, "SMPL_HLDR.RECT", (  -7000, 7000, 7000, -2000 ))
	dct_put(dct, "fpath", fpath)
	return(dct)
