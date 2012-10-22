#! /usr/bin/env python
"""Static blog generator"""

import jinja2
import markdown
import os
import yaml
import datetime
import shutil
import argparse
import collections
import lib.http

POST_SKELETON = """
title: "{title}"
date: {date}
categories:
---
"""


def generate_post_filepath(title, date):
    """Return the path a post should use based on its title and date"""
    post_file_date = datetime.datetime.strftime(date, '%Y/%m/%d/')
    title = ''.join(char for char in title.lower() if (
        char.isalnum() or char == ' '))
    return post_file_date + title.replace(' ', '-')


def get_all_posts(content_dir, blog_prefix, canonical_url, blog_root=None):
    """Return a list of dictionaries representing converted posts"""
    input_files = os.listdir(content_dir)
    all_posts = list()

    for post_file_name in input_files:
        if os.path.splitext(post_file_name)[1] != ".md":
            continue

        post_file_buffer = str()
        with open(os.path.join(content_dir, post_file_name), 'r', encoding='ascii') as post_file:
            post_file_buffer = post_file.read()

        # Split the file into the YAML front matter and the post proper
        (front_matter, _, post_body) = post_file_buffer.partition('\n---\n')
        post = yaml.load(front_matter)

        # Generate HTML from Markdown, splitting between the teaser (the
        # content to display on the front page until <!--more--> is reached)
        # and the post proper
        post['body'] = markdown.markdown(post_body, ['fenced_code',
            'codehilite', 'tables'])
        (teaser, _, _) = post['body'].partition('<!--more-->')
        post['teaser'] = teaser
        post['categories'] = post['categories'].split()

        # Construct datetime from the *incredibly useful* string YAML
        # provides
        post['date'] = datetime.datetime.strptime(
                (post['date'].strip()), '%Y-%m-%d %H:%M')

        # In general we know the layout on disk much match the generated urls
        # This doesn't hold in the case that there is an appendix to the
        # domain that the site resides on. For example, if my WidgetFactory
        # marketing department blog lived at
        # www.widgetfactory.com/marketing/blog/, we would generate the
        # files in the /blog sub-directory but the links would need to
        # include /marketing/blog
        post['relative_path'] = generate_post_filepath(post['title'],
                post['date']) + '/'
        if blog_prefix:
            post['relative_path'] = os.path.join(
                    blog_prefix, post['relative_path'])

        post['relative_url'] = '/' + post['relative_path']
        if blog_root:
            post['relative_url'] = os.path.join(
                    '/', blog_root, post['relative_url'])

        post['canonical_url'] = canonical_url + post['relative_url']

        all_posts.append(post)
    return all_posts


def create_path_to_file(path):
    """Given a path, make sure all intermediate directories exist; create
    them if they don't"""
    if not os.path.splitext(path)[1]:
        path += '/'
    else:
        path = os.path.dirname(path)
    if not os.path.exists(path):
        os.makedirs(path)


def generate_post(post, template_variables):
    """Generate a single post's HTML file"""
    output_path = os.path.join(template_variables['output_dir'],
            post['relative_path'], 'index.html')

    if not post['body']:
        raise EnvironmentError('No content for post [{post}] found.'.format(
            post=post['relative_path']))

    # Probably need a better value for 'description', but this will
    # do for now
    post['description'] = post['body'].split()[0]
    # Need to keep 'post' and 'site' variables separate
    post_vars = {'post': post}

    template_variables.update(post_vars)
    template = template_variables['env'].get_template('post.html')
    create_path_to_file(output_path)
    with open(output_path, 'w') as output:
        output.write(template.render(template_variables))


def generate_static_page(template_variables, output_dir, template_name,
        filename='index.html'):
    """Generate a static page"""
    template = template_variables['env'].get_template(template_name)
    create_path_to_file(output_dir)
    with open(os.path.join(output_dir, filename), 'w', encoding='ascii') as output_file:
        output_file.write(template.render(template_variables))


def generate_static_files(site_config):
    """Generate all 'static' files, files not based on markdown conversion"""
    # Not sure if this is Octopress silliness, but generate an index.html
    # at both the root level and the 'blog' level, so both www.foo.com and
    # www.foo.com/blog can serve the blog
    generate_static_page(site_config,
            site_config['output_dir'], 'index.html')
    generate_static_page(site_config,
            site_config['blog_dir'], 'index.html')
    generate_static_page(site_config,
            os.path.join(site_config['blog_dir'],
                'archives'), 'archives.html')
    generate_static_page(site_config,
            os.path.join(site_config['output_dir'],
                'about-me'), 'about.html')
    generate_static_page(site_config, site_config['output_dir'],
                'atom.xml', 'atom.xml')
    for category, posts in site_config['categories'].items():
        site_config['all_posts'] = posts
        generate_static_page(site_config, os.path.join(site_config['blog_dir'],
            'categories', category), 'archives.html')
        generate_static_page(site_config, os.path.join(site_config['blog_dir'],
            'categories', category), 'atom.xml', 'atom.xml')


def generate_pagination_pages(site_config):
    """Generate the additional index.html files required for pagination"""
    current_page = 1
    all_posts = site_config['all_posts']
    for page in [all_posts[index:index + 5] for index in range(
        5, len(all_posts), 5)]:
        current_page += 1
        # Since we're reusing the index.html template, make it think
        # these posts are the only ones
        site_config['all_posts'] = page
        output_dir = os.path.join(site_config['blog_dir'],
                'page', str(current_page))
        generate_static_page(site_config, output_dir, 'index.html')


def generate_all_files(site_config):
    """Generate all HTML files from the content directory using the sitewide
    configuration"""
    all_posts = get_all_posts(site_config['content_dir'],
            site_config['blog_prefix'], site_config['url'],
            site_config['blog_root'])
    all_posts.sort(key=lambda i: i['date'], reverse=True)
    categories = collections.defaultdict(list)
    for post in all_posts:
        for category in post['categories']:
            categories[category].append(post)

    site_config['now'] = datetime.datetime.now().isoformat()
    site_config['recent_posts'] = all_posts[:5]
    site_config['all_posts'] = all_posts
    site_config['categories'] = categories
    site_config['env'] = jinja2.Environment(
            loader=jinja2.FileSystemLoader(site_config['template_dir']))

    generate_static_files(site_config)
    generate_pagination_pages(site_config)

    for index, post in enumerate(all_posts):
        try:
            post['post_previous'] = all_posts[index + 1]
        except:
            post['post_previous'] = all_posts[0]
        generate_post(post, site_config)


def copy_static_content(output_dir, root_dir):
    """Copy (if necessary) the static content to the appropriate directory"""
    if os.path.exists(output_dir):
        print ('Removing old content...')
        shutil.rmtree(output_dir)
    shutil.copytree(os.path.join(root_dir, 'static'), output_dir)


def create_post(title, content_dir):
    """Create an empty post with the YAML front matter generated"""
    post_file_name = generate_post_filepath(title, datetime.datetime.now())
    post_file_name = post_file_name.replace('/', '-') + '.md'

    post_date = datetime.datetime.strftime(
            datetime.datetime.now(), '%Y-%m-%d %H:%M')

    if os.path.exists(os.path.join(content_dir, post_file_name)):
        raise EnvironmentError(
                '[{post}] already exists.'.format(post=post_file_name))

    with open(os.path.join(content_dir, post_file_name), 'w') as post_file:
        post_file.write(POST_SKELETON.format(date=post_date, title=title))


def serve(*args, **kwargs):
    """Serve static HTML pages indefinately"""

    root = kwargs['root']
    os.chdir(root)
    handler = lib.http.FileCacheRequestHandler

    httpd = lib.http.BlugHttpServer(root, (kwargs['host'], int(kwargs['port'])),
            handler)

    print("serving from {path} on port {port}".format(path=root,
        port=kwargs['port']))

    while True:
        httpd.handle_request()


def run_server(httpd):
    for x in range(10000):
        httpd.handle_request()


def create_new_post(*args, **kwargs):
    site_config = dict()
    config_file = 'config.yml'
    if os.path.exists('config.local.yml'):
        config_file = 'config.local.yml'
    with open(config_file, 'r') as config_file_handle:
        site_config = yaml.load(config_file_handle.read())
    create_post(kwargs['title'], site_config['content_dir'])


def generate_site(*args, **kwargs):
    site_config = dict()
    config_file = 'config.yml'
    if os.path.exists('config.local.yml'):
        config_file = 'config.local.yml'
    with open(config_file, 'r') as config_file_handle:
        site_config = yaml.load(config_file_handle.read())

    site_config['blog_dir'] = site_config['output_dir']
    if 'blog_prefix' in site_config:
        site_config['blog_dir'] = os.path.join(site_config['output_dir'],
            site_config['blog_prefix'])
    print ('Generating...')

    copy_static_content(site_config['output_dir'], os.getcwd())
    generate_all_files(site_config)


def main():
    """Main execution of blug"""
    argument_parser = argparse.ArgumentParser(
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            description='Generate a static HTML blog from \
                    Markdown blog entries')
    subparser = argument_parser.add_subparsers(help='help for sub-commands')

    post_parser = subparser.add_parser('post', help='Create a blank blog post',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    post_parser.add_argument('title',
            help='Title for the blog post to be generated')
    post_parser.set_defaults(func=create_new_post)

    generate_parser = subparser.add_parser('generate',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            help='Generate the complete static site using the posts\
                    in the \'content\' directory')
    generate_parser.set_defaults(func=generate_site)

    serve_parser = subparser.add_parser('serve',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            help='Start an HTTP server that serves the files under the \
                    <content-dir> directory')
    serve_parser.add_argument('-p', '--port', default=8080,
            help='Port for HTTP server to listen to')
    serve_parser.add_argument('-s', '--host', action='store',
            default='localhost',
            help='Hostname for HTTP server to serve on')
    serve_parser.add_argument('-r', '--root', action='store',
            default=os.path.join(os.getcwd(), 'generated'),
            help='Root path to serve files from')
    serve_parser.set_defaults(func=serve)

    arguments = argument_parser.parse_args()

    argument_dict = vars(arguments)
    arguments.func(**argument_dict)
    print ('Complete')


if __name__ == '__main__':
    main()
