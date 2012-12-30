from bottle import request, response, route, run, static_file
import local_pil
from local_wand.image import Image
from local_wand.color import Color
import local_wand.api, local_wand.image, local_wand.color
import os, glob, re, ctypes
from cStringIO import StringIO

imagelist=[]

@route('/images/<filename:re:.*\.png>')
def send_image(filename):
  return static_file(filename, root='images', mimetype='image/png')

@route('/pilgif/<filename:re:.*\.png>')
def pil_asgif(filename):
  img = local_pil.Image.open(os.path.join('images', filename))
  img = img.convert('RGB')
  img = img.convert('P', palette=Image.ADAPTIVE, colors=255)
  gif = StringIO()
  img.save(gif, 'GIF', transparency=255)
  response.content_type = 'image/gif'
  return gif.getvalue()

def img(filename):
  return Image(filename=os.path.join('images', filename))

@route('/gif/<filename:re:.*\.png>')
def asgif_auto(filename):
  return asgif(img(filename))

@route('/remove/<filename:re:.*\.png>')
def remove(filename):
  if filename in imagelist:
    os.rename(os.path.join('images', filename), os.path.join('images', filename+'.removed'))
    return show_index('%s removed' % (filename))
  return show_index('%s not found' % (filename))

def asgif(img):
  gif = StringIO()
  img.format = 'gif'
  img.save(file=gif)
  response.content_type = 'image/gif'
  return gif.getvalue()

@route('/tgif/<filename:re:.*\.png>')
def asgif_threshold(filename):
  im = img(filename)
  alpha = im.alpha_channel
  im.background_color = Color(request.query.bg or '#ffffff')
  local_wand.api.library.MagickSetImageAlphaChannel(im.wand, local_wand.image.ALPHA_CHANNEL_TYPES.index('flatten'))

  local_wand.api.library.MagickTransparentPaintImage.restype = ctypes.c_bool
  local_wand.api.library.MagickTransparentPaintImage.argtypes = [
    ctypes.c_void_p, ctypes.c_void_p, ctypes.c_double, ctypes.c_double, ctypes.c_bool]

  pixel = local_wand.api.library.NewPixelWand()
  local_wand.api.library.PixelSetColor(pixel, request.query.tc or '#ff00ff')
  local_wand.api.library.MagickTransparentPaintImage(im.wand, pixel, 0.0, 0, False)
  return asgif(im)

@route('/upload', method='POST')
def do_upload():
  data = request.files.get('data')
  raw = data.file.read()
  filename = data.filename
  f = open(os.path.join('images', filename), 'w')
  f.write(raw)
  f.close()
  return show_index('You uploaded %s (%d bytes).' % (filename, len(raw)))

@route('/')
def show_index(msg=''):
  refresh_list()
  lis = '\n'.join([('<tr><td><a href="/preview/{0}?{1}" title="Preview">' +
                      '<img alt="{0}" src="/images/{0}?{1}" />' +
                    '</a></td>'+
                    '<td><img alt="{0}" src="/gif/{0}?{1}" /></td>' +
                    '<td><img alt="{0}" src="/tgif/{0}?{1}" /></td>' +
                    '<td>{0} <a href="/remove/{0}?{1}">remove</a></td>'
                    '</tr>').format(x, request.query_string)
                  for x in imagelist])
  return """
<style>
img {
  image-rendering: -webkit-optimize-contrast;
  border: solid;
}
</style>
<p>%s</p>
<h2>Settings</h2>
<form action="/" method="get" enctype="multipart/form-data">
  <ul>
  <li>Page background Color: <input type="color" value="%s" id="pbg" name="pbg" onchange="document.body.style.backgroundColor=this.value"></li>
  <li>Image background Color: <input type="color" value="%s" id="bg" name="bg" onchange="this.form.submit()"> (close dialog after changing)</li>
  <li>Transparent Color: <input type="color" value="%s" id="tc" name="tc" onchange="this.form.submit()"> (close dialog after changing)</li>
  <li>Zoom: <input type="range" name="zoom" step="0.1" min="1.0" max="10.0" value="%s" onchange="rezoom(this.value)"><br />
    Note: "zoom" isn't that useful because Chrome doesn't support CSS image-rendering:pixelated. See
    <a href="https://developer.mozilla.org/en-US/docs/CSS/image-rendering">https://developer.mozilla.org/en-US/docs/CSS/image-rendering</a>.</li>
  </ul>
</form>
<h2>Add a new file</h2>
<form action="/upload" method="post" enctype="multipart/form-data">
  <input type="file" name="data" />
  <input type="submit" value="Upload" />
</form>
<h2>Images - click for 8-bit preview</h2>
<table>
<thead><tr><td>PNG</td><td>8-bit (threshold)</td><td>8-bit (flatten)</td><td>file</td></tr></thead>
<tbody>
%s
</tbody>
</table>
<script>
function rezoom(ratio) {
  var imgs = document.querySelectorAll('img');
  for (var idx = 0; idx < imgs.length; ++idx) {
    var i = imgs[idx];
    i.style.width = 'auto';
    i.style.height = 'auto';
    var w = i.width * ratio;
    var h = i.height * ratio;
    i.style.width = w + 'px';
    i.style.height = h + 'px';
  }
}
document.body.style.backgroundColor = document.getElementById('pbg').value;
</script>
""" % (msg,
       request.query.pbg or '#00ffff',
       request.query.bg or '#ffffff',
       request.query.tc or '#ff00ff',
       request.query.zoom or '1.0',
       lis)

@route('/preview/<filename>')
def preview(filename):
  return 'todo'

digitre = re.compile('[0-9]+')
def sortkey(v):
  m = digitre.search(v)
  return m and int(m.group(0)) or v

def refresh_list():
  global imagelist
  imagelist = []
  for dirname, dirnames, filenames in os.walk('images'):
    for img in filenames:
      if img[-4:] == '.png':
        imagelist.append(img)
  iamgelist = imagelist.sort(key=sortkey)

run(host='localhost', port=8080)
