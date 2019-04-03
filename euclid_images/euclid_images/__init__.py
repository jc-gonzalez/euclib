import os
logging_modules = ''
if 'LOGGING_MODULES' in os.environ:
    logging_modules = os.environ['LOGGING_MODULES'] + ':'
add_modules = [ __name__ + '.' + x for x in
                ['euclid_image', 'vis_image', 'vis_image.VIS_Image']]
os.environ['LOGGING_MODULES'] = logging_modules + ':'.join(add_modules)
print(os.environ['LOGGING_MODULES'])