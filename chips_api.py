from flask import Flask, render_template
# -------------------- #
# Date：2024-2-2
# Author：AlexChing
# Function: Web Application
# -------------------- #
app = Flask(__name__)
image_folder = 'images'

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True,port=49999,host='0.0.0.0')
