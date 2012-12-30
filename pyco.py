from bottle import request, response, route, run, static_file
import local_pil
from local_wand.image import Image
import os, glob, re
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
  im.alpha_channel = False
  #img = img.convert('RGB')
  #img = img.convert('P', palette=Image.ADAPTIVE, colors=255)
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

@route('/', method='GET')
def show_index(msg=''):
  refresh_list()
  lis = '\n'.join([('<tr><td><a href="/preview/{0}" title="Preview">' +
                      '<img alt="{0}" src="/images/{0}" />' +
                    '</a></td>'+
                    '<td><img alt="{0}" src="/gif/{0}" /></td>' +
                    '<td><img alt="{0}" src="/tgif/{0}" /></td>' +
                    '<td>{0} <a href="/remove/{0}">remove</a></td>'
                    '</tr>').format(x)
                  for x in imagelist])
  return """
<style>
img {
  image-rendering: -webkit-optimize-contrast;
  border: solid;
}
</style>
<p>%s</p>
<form action="/upload" method="post" enctype="multipart/form-data">
<h2>Settings</h2>
  <ul>
  <li>Background Color: <input type="color" name="bg" onchange="document.body.style.backgroundColor=this.value"></li>
  <li>Transparent Color:</li>
  <li>Zoom: <input type="range" name="zoom" step="0.1" min="1.0" max="4.1" value="1.0" onchange="rezoom(this.value)"><br />
    Note: "zoom" isn't that useful because Chrome doesn't support CSS image-rendering:pixelated. See
    <a href="https://developer.mozilla.org/en-US/docs/CSS/image-rendering">https://developer.mozilla.org/en-US/docs/CSS/image-rendering</a>.</li>
  </ul>
<h2>Add a new file</h2>
  <input type="file" name="data" />
  <input type="submit" value="Upload" />
</form>
<h2>Images - click for 8-bit preview</h2>
<table>
<thead><tr><td>PNG</td><td>8-bit (auto)</td><td>8-bit (manual)</td><td>file</td></tr></thead>
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
</script>
""" % (msg, lis)

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
