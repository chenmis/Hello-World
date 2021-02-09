from flask import Flask, render_template

app = Flask(__name__)

@app.route('/home/')
@app.route('/home')
@app.route('/')
def HomePage():
    return render_template("CV-Grid.html")

@app.route('/ContactList')
@app.route('/contactlist')
def UsersListPage():
    return render_template("ContactList.html")

@app.route('/assignment8')
@app.route('/assignment8/')
def assignment8():
    return render_template('assignment8.html', Books=[
        'Harry Potter & Philosophers Stone', 'Harry Potter & Chamber of Secrets', 'Harry Potter & Prisoner of Azkaban', 'Harry Potter & Goblet of Fire', 'Harry Potter & Order of the Phoenix', 'Harry Potter & Half-Blood Prince', 'Harry Potter & Deathly Hallows'
    ], )

if __name__ == '__main__':
    app.run(debug=True)
