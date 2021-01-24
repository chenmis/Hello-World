from flask import Flask,redirect,url_for

app = Flask(__name__)


@app.route('/')
def hello():
    return redirect("http://www.google.com")

@app.route('/main')
def go_to_main():
    return redirect(url_for('hello'))

if __name__ == '__main__':
    app.run()
