from fabric.api import put, sudo, local, run, cd, prefix, task, abort, env
from fabric.contrib.console import confirm
import os.path
import sys


def load_settings():
    import yaml
    if os.path.exists('config.local.yml'):
        config_file = 'config.local.yml'
    with open(config_file) as config_file_handle:
        site_config = yaml.load(config_file_handle.read())

    env.blug_content_dir = site_config['output_dir']
    env.public_html_dir = site_config['public_html_dir']
    env.remote_staging_dir = site_config['remote_staging_dir']


@task
def check_git_status():
    status_lines = local('git status --porcelain', capture=True)
    if status_lines and not confirm('Working directory not clean! Deploy anyway?'):
            abort('Working directory not clean')


@task
def generate_site():
    with prefix('source /usr/bin/virtualenvwrapper.sh'), prefix('workon blug'):
        local('python blug.py generate')


def copy_to_remote():
    load_settings()
    check_git_status()
    if not os.path.exists(env.blug_content_dir):
        sys.exit('{} is not a valid path on the local machine'.format(env.blug_content_dir))
    if os.path.exists('content.tar.gz'):
        os.unlink('content.tar.gz')
    local('tar -cf content.tar ' + env.blug_content_dir)
    local('gzip content.tar')
    with cd(env.remote_staging_dir):
        run('rm -rf *')
        put('content.tar.gz', env.remote_staging_dir)
        run('tar -xzf content.tar.gz')
        sudo('rm -rf {public_html_dir}/*'.format(public_html_dir=env.public_html_dir))
        sudo('cp -rp {source}/* {dest}'.format(source=env.blug_content_dir, dest=env.public_html_dir))


@task
def deploy():
    generate_site()
    copy_to_remote()
