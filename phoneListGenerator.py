# File to create the bon-APP-etit website
from flask import Flask, render_template, request, redirect, url_for
from jacobs_dir_scraper import read_jsoe_dir, format_table
ERR_NO_OPTS = 0
ERR_NO_FILE = 1

app = Flask(__name__)

@app.route('/')
def home():
  return render_template('home.html')

@app.route('/generator/', methods=['GET', 'POST'])
def generateList():
  print("hi")
  prev = request.form.get('uploadPrev')
  fileName = None 
  if (prev):
    fileName = request.form['fileName']
  check = request.form.get('blinkCheck')
  create = request.form.get('newList')

  if not (prev or check or create):
    return redirect(url_for('optErrors', errorCode=ERR_NO_OPTS))

  elif prev and not fileName:
    return redirect(url_for('optErrors', errorCode=ERR_NO_FILE))

  else:
    [people_table, names, header_map] = read_jsoe_dir(create, check, prev, fileName)
    # TODO call checkBlink here if check
    people_list = format_table(people_table, names, header_map)
    return render_template('generator.html', result = people_list)

@app.route('/error/', methods=['GET', 'POST'])
def optErrors():
  return render_template('error.html', code=request.args['errorCode'])

if __name__ == '__main__':
  app.run()
