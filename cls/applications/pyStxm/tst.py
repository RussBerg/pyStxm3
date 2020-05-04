from cls.utils.file_system_tools import get_next_file_num_in_seq
data_dir = r'S:\STXM-data\Cryo-STXM\2020\guest\0318'
print('C' + str(get_next_file_num_in_seq(data_dir, extension='hdf5')))
