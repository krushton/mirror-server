import os,os.path,json,redis

from flask import Flask,request,Response,render_template
from boto.s3.connection import S3Connection,Key
from threading import Timer

app = Flask(__name__)
AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY_ID')       
AWS_SECRET_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
S3_BUCKET = os.environ.get('S3_BUCKET')

redis_url = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')
redis = redis.from_url(redis_url)

conn = S3Connection(AWS_ACCESS_KEY, AWS_SECRET_KEY)

#main page that shows latest images in a grid
@app.route('/')
def index():
    urls = get_urls()
    return render_template('index.html',images=urls)

#route for ajax calls from main page
@app.route('/getimages')
def find():
    urls = get_urls()
    d = json.dumps(urls)
    resp = Response(response=d, status=200, mimetype="application/json")
    return resp

#route that accepts images from the android app
@app.route('/postfiles', methods=['POST'])
def post():
    data = request.form 
    files = request.files

    # adds a modicum of security... 
    code = data.get('code')
    if code != os.environ.get('SEKKRIT_CODE'):
        err = Response(response="{'error':'unauthorized'}", status=401, mimetype="application/json")
        return err
    
    f = files.get('image')
    b = conn.get_bucket(S3_BUCKET)
    k = Key(b)
    
    path = data.get('filename')
    k.key = path
    k.set_contents_from_file(f)
    k.set_acl("public-read")

    #update the list of URLs stored in redis
    get_latest()

    #return the file name because reasons
    return json.dumps({"file" : path})

def get_urls():
    f = redis.get('urls')
    urls = json.loads(f)
    return urls

def get_latest():
    #runs in separate thread
    with app.test_request_context():
        b = conn.get_bucket(S3_BUCKET)

        #sort the keys by last modified
        m_list = []
        for item in b.list():
            m_list.append(item)

        m_list.sort(key=lambda x: x.last_modified)
        latest_keys = m_list[-8:]

        #get a s3 url for each image key
        urls = []
        for key in latest_keys:
            urls.append(key.generate_url(86400))
        
        redis.set('urls', json.dumps(urls))

if __name__ == '__main__':
    app.debug = True
    port = int(os.environ.get('PORT', 5000))
    get_latest()
    app.run(host='0.0.0.0', port=port)   #heroku


