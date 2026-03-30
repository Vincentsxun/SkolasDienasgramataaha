from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

# @app.route("/gallery")
# def gallery():
#     return render_template("gallery.html")

# @app.route("/about")
# def about():
#     return "<h1>Par šo projektu</h1><p>Šis ir piemērs ar vairākām lapām.</p>"

if __name__ == "__main__":
    app.run(debug=True)