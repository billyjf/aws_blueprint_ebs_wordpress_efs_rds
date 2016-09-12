#!/usr/bin/python
# Last tested on 2.7.10
import argparse
import urllib, urllib2
import os
from zipfile import ZipFile
from os import listdir
from os.path import isfile, join
import re
import shutil

parser = argparse.ArgumentParser(description="""
Download wordpress, populate keys.config with new salts, 
and generate an easily configurable ElasticBeanstalk package for managing 
multiple Wordpress installs using a single rds, efs, and multiple Beanstalk 
environment configs.""")
parser.add_argument('-s', '--site-name', 
                    type=str, 
                    help='The site name to include in the output package file name ' + \
                    '(e.g. wordpress-x.x_efs_rds_[site-name]_xx.zip).',
                    required=True)
parser.add_argument('-b', '--build-number',
                    type=int,
                    help="Set the starting build number.",
                    default=1)

args = parser.parse_args()

script_dir = os.path.dirname(os.path.realpath(__file__))

#
# Establish Wordpress Dir
#
if not os.path.exists('{0}/wordpress'.format(script_dir)):
    print "Could not find wordpress directory, downloading latest ..."
    local_filename, headers = urllib.urlretrieve('https://www.wordpress.org/latest.zip')

    with ZipFile(local_filename) as zip:
        zip.extractall()  # Establish wordpress dir

    zip_filename = headers.getheader('Content-Disposition').split('=')[1]

    os.rename(local_filename, 
              '{0}/{1}'.format(script_dir, zip_filename))

    os.mkdir('wordpress/.ebextensions')

    #
    # Salt keys.config
    #
    print "Salting keys.config ..."
    r = urllib2.urlopen('https://api.wordpress.org/secret-key/1.1/salt/')
    salt = r.read()

    salts = {'AUTH_KEY': re.search("'AUTH_KEY', .*'(.*)'", salt).group(1),
             'SECURE_AUTH_KEY': re.search("'SECURE_AUTH_KEY', .*'(.*)'", salt).group(1),
             'LOGGED_IN_KEY': re.search("'LOGGED_IN_KEY', .*'(.*)'", salt).group(1),
             'NONCE_KEY': re.search("'NONCE_KEY', .*'(.*)'", salt).group(1),
             'AUTH_SALT': re.search("'AUTH_SALT', .*'(.*)'", salt).group(1),
             'SECURE_AUTH_SALT': re.search("'SECURE_AUTH_SALT', .*'(.*)'", salt).group(1),
             'LOGGED_IN_SALT': re.search("'LOGGED_IN_SALT', .*'(.*)'", salt).group(1),
             'NONCE_SALT': re.search("'NONCE_SALT', .*'(.*)'", salt).group(1)}

    with open('wordpress/.ebextensions/keys.config', 'w') as file:
        file.write("""option settings:
      - option name: AUTH_KEY
        value: '{0}'
      - option name: SECURE_AUTH_KEY
        value: '{1}'
      - option name: LOGGED_IN_KEY
        value: '{2}'
      - option name: NONCE_KEY
        value: '{3}'
      - option name: AUTH_SALT
        value: '{4}'
      - option name: SECURE_AUTH_SALT
        value: '{5}'
      - option name: LOGGED_IN_SALT
        value: '{6}'
      - option name: NONCE_SALT
        value: '{7}'""".format(salts['AUTH_KEY'],
                               salts['SECURE_AUTH_KEY'],
                               salts['LOGGED_IN_KEY'],
                               salts['NONCE_KEY'],
                               salts['AUTH_SALT'],
                               salts['SECURE_AUTH_SALT'],
                               salts['LOGGED_IN_SALT'],
                               salts['NONCE_SALT']))

# Files are always re-copied, per build
shutil.copy('.ebextensions/commands.config', 'wordpress/.ebextensions')
shutil.copy('wp-config.php', 'wordpress')

#
# Final ElasticBeanstalk deployable zip archive
#
print "Generating ElasticBeanstalk deployable archive ..."
build_number = args.build_number
wordpress_zip_files = [f for f in listdir(script_dir) \
                       if isfile(join(script_dir, f)) and \
                       'wordpress' in f and '.zip' in f]

export_base_filename = '{0}_efs_rds_{1}'.format(
    wordpress_zip_files[0].split('.zip')[0],
    args.site_name)

prior_build_numbers = [int(f[f.rindex('_')+1:].split('.zip')[0]) for f \
                       in listdir(script_dir) \
                       if isfile(join(script_dir, f)) and \
                       export_base_filename in f and \
                       '.zip' in f]

if len(prior_build_numbers) > 0:
    build_number = max(prior_build_numbers) + 1

export_filename = '{0}_{1}.zip'.format(export_base_filename, 
    build_number)

with ZipFile(export_filename, 'w') as zip_file:
    for root, dirs, files in os.walk('wordpress'):
        for file in files:
            file_path = join(root, file)
            zip_file.write(file_path, 
                           file_path.replace('wordpress' + os.sep, ''))
