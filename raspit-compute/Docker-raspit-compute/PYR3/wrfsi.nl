&project_id
 SIMULATION_NAME = 'Pyrenees domain 3'
 USER_DESC = 'Max'
/
&filetimespec
 START_YEAR = 2002,
 START_MONTH = 05,
 START_DAY = 13,
 START_HOUR = 12,
 START_MINUTE = 00,
 START_SECOND = 00,
 END_YEAR = 2002,
 END_MONTH = 05,
 END_DAY = 14,
 END_HOUR = 00,
 END_MINUTE = 00,
 END_SECOND = 00,
 INTERVAL = 10800
/
&hgridspec
 NUM_DOMAINS = 2
 XDIM = 202
 YDIM = 172
 PARENT_ID = 1, 1
 RATIO_TO_PARENT = 1, 3
 DOMAIN_ORIGIN_LLI = 1, 66
 DOMAIN_ORIGIN_LLJ = 1, 63
 DOMAIN_ORIGIN_URI = 202, 133
 DOMAIN_ORIGIN_URJ = 172, 115
 MAP_PROJ_NAME = 'lambert'
 MOAD_KNOWN_LAT = 43.5
 MOAD_KNOWN_LON = 0.87
 MOAD_STAND_LATS = 44.61, 44.61
 MOAD_STAND_LONS = 0.87
 MOAD_DELTA_X = 9000
 MOAD_DELTA_Y = 9000
 SILAVWT_PARM_WRF = 0.
 TOPTWVL_PARM_WRF = 2.
/
&sfcfiles
 TOPO_30S = '/root/DRJACK/WRF/wrfsi/extdata/GEOG/topo_30s',
 LANDUSE_30S = '/root/DRJACK/WRF/wrfsi/extdata/GEOG/landuse_30s',
 SOILTYPE_TOP_30S = '/root/DRJACK/WRF/wrfsi/extdata/GEOG/soiltype_top_30s',
 SOILTYPE_BOT_30S = '/root/DRJACK/WRF/wrfsi/extdata/GEOG/soiltype_bot_30s',
 GREENFRAC = '/root/DRJACK/WRF/wrfsi/extdata/GEOG/greenfrac',
 SOILTEMP_1DEG = '/root/DRJACK/WRF/wrfsi/extdata/GEOG/soiltemp_1deg',
 ALBEDO_NCEP = '/root/DRJACK/WRF/wrfsi/extdata/GEOG/albedo_ncep',
 MAXSNOWALB = '/root/DRJACK/WRF/wrfsi/extdata/GEOG/maxsnowalb',
 ISLOPE = '/root/DRJACK/WRF/wrfsi/extdata/GEOG/islope',
/
&interp_control
 NUM_ACTIVE_SUBNESTS = 0,
 ACTIVE_SUBNESTS = 2,3,4,
 PTOP_PA = 5000,
 HINTERP_METHOD = 1,
 LSM_HINTERP_METHOD = 1,
 NUM_INIT_TIMES = 1, 
 INIT_ROOT = 'ETA',
 LBC_ROOT = 'ETA',
 LSM_ROOT = '',
 CONSTANTS_FULL_NAME = '',
 VERBOSE_LOG = .false.,
 OUTPUT_COORD = 'ETAP',
 LEVELS = 1.000, 0.998, 0.994, 0.987, 0.979, 
	0.969, 0.958, 0.945, 0.933, 0.920, 
	0.907, 0.895, 0.882, 0.870, 0.857, 
	0.844, 0.830, 0.817, 0.804, 0.790, 
	0.776, 0.762, 0.747, 0.731, 0.715, 
	0.699, 0.681, 0.663, 0.642, 0.617, 
	0.585, 0.549, 0.508, 0.463, 0.420, 
	0.381, 0.347, 0.321, 0.300, 0.279, 
	0.257, 0.236, 0.213, 0.191, 0.168, 
	0.145, 0.122, 0.098, 0.074, 0.050, 
	0.025, 0.000
/
&si_paths
 ANALPATH = '/root/DRJACK/WRF/wrfsi/extdata/extprd',
 LBCPATH = '/root/DRJACK/WRF/wrfsi/extdata/extprd',
 LSMPATH = '/root/DRJACK/WRF/wrfsi/extdata/extprd',
 CONSTANTS_PATH = '/root/DRJACK/WRF/wrfsi/extdata/extprd',
/
