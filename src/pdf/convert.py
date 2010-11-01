import subprocess
import tempfile
import logging
import re
import os


IMAGE_GEOMETRY = re.compile(r'(\d+)x(\d+)\+(\d+)\+(\d+)')


def get_dimensions(filename):
    logging.info('getting dimensions for %s', filename)
    p = subprocess.Popen(['identify', '-format', '%g', filename],
                         stdout=subprocess.PIPE)
    dimensions = p.stdout.read()
    logging.info('%s has dimensions %s', filename, dimensions.strip())
    m = IMAGE_GEOMETRY.match(dimensions)
    if m:
        return map(int, m.groups())

def convert_pdf(input, output, dimension, image_type='png'):
    """
    Converts the input (a PDF file) into an image.
    :param input: The input filename.
    :param output: The output filename.
    :param dimension: The desired dimension. A tuple of (width, height)
    :param image_type: One of png or jpg. Selects the output format.
    """
    width, height, _, _ = get_dimensions(input)
    logging.info('Scaling to %s', dimension)
    # Target width and height
    t_width, t_height = dimension
    width_ratio = float(t_width) / width
    height_ratio = float(t_height) / height
    logging.debug('width ratio %f height ratio %f', width_ratio, height_ratio)
    if width_ratio >= height_ratio:
        # Scale height
        abc_w = None
        abc_h = t_height
    else:
        abc_w = t_width
        abc_h = None

    temp_fd, temp = tempfile.mkstemp(suffix='.%s' % image_type)
    try:
        resize(input, temp, width=abc_w, height=abc_h)
        extent(temp, output, '%dx%d' % dimension)
    except Exception, e:
        print e
        pass
    logging.info('removing tempfile %s', temp)
    os.remove(temp)
    logging.info('converted %s -> %s', input, output)


def convert_pdf_to_dir(input, output_dir, dimension, image_type='png'):
    """
    Converts the input (a PDF file) into an image.
    :param input: The input filename.
    :param output_dir: The output directory.
    :param image_type: One of png or jpg. Selects the output format.
    """
    # Split off the file extension.
    basename = input.rsplit('.', 1)[0]
    # Construct the output filename.
    output = os.path.join(output_dir, '%s.%s' % (basename, image_type))
    convert_pdf(input, output, dimension, image_type=image_type)


def resize(input, output, width=None, height=None):
    if not height and width:
        dimension = '%d' % width
    elif not width and height:
        dimension = 'x%d' % height
    elif width and height:
        dimension = '%dx%d' % (width, height)
    else:
        # Nothing to be done.
        return
    logging.info('resizing %s -> %s to %s', input, output, dimension)
    p = subprocess.Popen(['convert', '-resize', dimension, input, output])
    exit_code = p.wait()
    logging.debug('resize exit code = %d', exit_code)
    if exit_code == 0:
        logging.debug('resizing was successful.')
    else:
        logging.info('resizing failed.')


def extent(input, output, geometry, gravity='Center',
           background='rgb(0,0,0)'):
    p = subprocess.Popen(['convert', '-extent', geometry, '-gravity', gravity,
                          '-background', background, input, output])
    exit_code = p.wait()
    logging.debug('resize exit code = %d', exit_code)
    if exit_code == 0:
        logging.debug('extent was successful.')
    else:
        logging.info('extent failed.')


# logging.basicConfig(level=logging.DEBUG)
# convert_pdf('input.pdf', 'output.png', (600, 1080))
# XXX To use this install ``imagemagick``
