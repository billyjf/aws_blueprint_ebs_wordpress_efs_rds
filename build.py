#!/usr/bin/python
# Last tested on 2.7.10
import argparse
import os
import urllib.request
from zipfile import ZipFile
from os import listdir
from os.path import isfile, join
import re
import shutil


def get_wordpress_salts():
    with urllib.request.urlopen('https://api.wordpress.org/secret-key/1.1/salt/') as s:
        salts_from_api = s.read().decode('utf-8')

    salts = {'AUTH_KEY': re.search("'AUTH_KEY', .*'(.*)'", salts_from_api).group(1),
             'SECURE_AUTH_KEY': re.search("'SECURE_AUTH_KEY', .*'(.*)'", salts_from_api).group(1),
             'LOGGED_IN_KEY': re.search("'LOGGED_IN_KEY', .*'(.*)'", salts_from_api).group(1),
             'NONCE_KEY': re.search("'NONCE_KEY', .*'(.*)'", salts_from_api).group(1),
             'AUTH_SALT': re.search("'AUTH_SALT', .*'(.*)'", salts_from_api).group(1),
             'SECURE_AUTH_SALT': re.search("'SECURE_AUTH_SALT', .*'(.*)'", salts_from_api).group(1),
             'LOGGED_IN_SALT': re.search("'LOGGED_IN_SALT', .*'(.*)'", salts_from_api).group(1),
             'NONCE_SALT': re.search("'NONCE_SALT', .*'(.*)'", salts_from_api).group(1)}

    return salts


def establish_wordpress_dir():
    script_dir = os.path.dirname(os.path.realpath(__file__))

    if not os.path.exists('{0}/wordpress'.format(script_dir)):
        print("Could not find wordpress directory, downloading latest...")
        local_filename, headers = urllib.request.urlretrieve('https://www.wordpress.org/latest.zip')
        with ZipFile(local_filename) as zip:
            zip.extractall()  # Establish wordpress dir

        zip_filename = headers.get('Content-Disposition').split('=')[-1]

        os.rename(local_filename, '{0}/{1}'.format(script_dir, zip_filename))

        os.mkdir('wordpress/.ebextensions')


def get_cli_args():
    parser = argparse.ArgumentParser(description="""
    Download wordpress, populate keys.config with new wordpress_salts, 
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

    return args


if __name__ == "__main__":
    args = get_cli_args()
    script_dir = os.path.dirname(os.path.realpath(__file__))

    establish_wordpress_dir()

    print("Salting keys.config ...")
    wordpress_salts = get_wordpress_salts()

    with open('wordpress/.ebextensions/keys.config', 'w') as file:
        with open('.ebextensions/keys.config', 'r') as keys_template:
            file.write(keys_template.read().format(wordpress_salts['AUTH_KEY'],
                                                   wordpress_salts['SECURE_AUTH_KEY'],
                                                   wordpress_salts['LOGGED_IN_KEY'],
                                                   wordpress_salts['NONCE_KEY'],
                                                   wordpress_salts['AUTH_SALT'],
                                                   wordpress_salts['SECURE_AUTH_SALT'],
                                                   wordpress_salts['LOGGED_IN_SALT'],
                                                   wordpress_salts['NONCE_SALT']).replace('`', '\`'))

    # Files are always re-copied, per build
    shutil.copy('.ebextensions/commands.config', 'wordpress/.ebextensions')
    shutil.copy('wp-config.php', 'wordpress')
    shutil.copy('.htaccess', 'wordpress')

    #
    # Final ElasticBeanstalk deployable zip archive
    #
    print("Generating ElasticBeanstalk deployable archive ...")
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
