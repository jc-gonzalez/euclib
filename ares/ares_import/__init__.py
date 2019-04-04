import os
logging_modules = ''
if 'LOGGING_MODULES' in os.environ:
    logging_modules = os.environ['LOGGING_MODULES'] + ':'
add_modules = [ __name__ + '.' + x for x in
                ['ares_import', 'ares_import.Importer']]
os.environ['LOGGING_MODULES'] = logging_modules + ':'.join(add_modules)
#print(os.environ['LOGGING_MODULES'])
